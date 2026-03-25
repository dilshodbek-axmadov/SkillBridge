import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, Loader2, Lock, UserPlus, Check } from 'lucide-react';
import useAuthStore from '../store/authStore';
import useRecruiterGate from '../hooks/useRecruiterGate';
import RecruiterLayout from '../components/layout/RecruiterLayout';
import api from '../services/api';

export default function RecruiterCandidateDetailPage() {
  useRecruiterGate();
  const { candidateId } = useParams();
  const user = useAuthStore((s) => s.user);

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const run = async () => {
      setLoading(true);
      setError('');
      try {
        const { data: d } = await api.get(`/recruiters/candidates/${candidateId}/`);
        setData(d);
        setSaved(false);
      } catch (e) {
        if (e.response?.status === 404) setError('Candidate not found or not visible to recruiters.');
        else setError('Could not load candidate.');
        setData(null);
      } finally {
        setLoading(false);
      }
    };
    if (candidateId) run();
  }, [candidateId]);

  const saveCandidate = async () => {
    if (!data?.id || saved) return;
    setSaving(true);
    try {
      await api.post('/recruiters/saved-candidates/', { candidate_id: data.id });
      setSaved(true);
    } catch {
      /* ignore */
    } finally {
      setSaving(false);
    }
  };

  const profile = data?.profile || {};
  const contactLocked = !data?.contact_unlocked;

  return (
    <RecruiterLayout user={user}>
      <Link
        to="/recruiter/candidates"
        className="inline-flex items-center gap-1.5 text-sm text-primary-600 hover:text-primary-700 no-underline mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to search
      </Link>

      {loading && (
        <div className="flex justify-center py-20">
          <Loader2 className="w-8 h-8 text-primary-600 animate-spin" />
        </div>
      )}

      {error && !loading && (
        <div className="rounded-xl border border-red-200 dark:border-red-900/50 bg-red-50 dark:bg-red-950/30 px-4 py-3 text-sm text-red-700 dark:text-red-300">
          {error}
        </div>
      )}

      {!loading && data && (
        <>
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-8">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{data.full_name}</h1>
              <p className="text-gray-600 dark:text-gray-300 mt-1">
                {[profile.desired_role || profile.current_job_position, profile.experience_level, profile.location]
                  .filter(Boolean)
                  .join(' · ')}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              {saved ? (
                <span className="inline-flex items-center gap-1 text-sm font-medium text-emerald-600 px-4 py-2 rounded-lg bg-emerald-50 dark:bg-emerald-950/40">
                  <Check className="w-4 h-4" />
                  On shortlist
                </span>
              ) : (
                <button
                  type="button"
                  onClick={saveCandidate}
                  disabled={saving}
                  className="inline-flex items-center gap-2 text-sm font-semibold text-white bg-primary-600 hover:bg-primary-700 px-4 py-2 rounded-lg border-none cursor-pointer disabled:opacity-60"
                >
                  <UserPlus className="w-4 h-4" />
                  {saving ? 'Saving…' : 'Save to shortlist'}
                </button>
              )}
            </div>
          </div>

          {contactLocked && (
            <div className="flex items-start gap-3 p-4 mb-6 rounded-xl bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900/50 text-sm text-amber-900 dark:text-amber-200">
              <Lock className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <p>
                Contact details are hidden on the Free recruiter plan. Upgrade to Pro to view email and phone when
                candidates opt in.
              </p>
            </div>
          )}

          <div className="grid lg:grid-cols-2 gap-6">
            <section className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-5">
              <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">Profile</h2>
              {profile.bio && <p className="text-sm text-gray-600 dark:text-gray-300 whitespace-pre-wrap">{profile.bio}</p>}
              <dl className="mt-4 space-y-2 text-sm">
                <div className="flex justify-between gap-4">
                  <dt className="text-gray-500">Email</dt>
                  <dd className="text-gray-900 dark:text-gray-100 text-right break-all">
                    {data.email || (contactLocked ? '—' : '—')}
                  </dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-gray-500">Phone</dt>
                  <dd className="text-gray-900 dark:text-gray-100">{data.phone || '—'}</dd>
                </div>
                {profile.linkedin_url && (
                  <div className="flex justify-between gap-4">
                    <dt className="text-gray-500">LinkedIn</dt>
                    <dd>
                      <a href={profile.linkedin_url} target="_blank" rel="noreferrer" className="text-primary-600">
                        Link
                      </a>
                    </dd>
                  </div>
                )}
                {profile.github_url && (
                  <div className="flex justify-between gap-4">
                    <dt className="text-gray-500">GitHub</dt>
                    <dd>
                      <a href={profile.github_url} target="_blank" rel="noreferrer" className="text-primary-600">
                        Link
                      </a>
                    </dd>
                  </div>
                )}
              </dl>
            </section>

            <section className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-5">
              <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">Skills</h2>
              {data.skills?.length ? (
                <ul className="flex flex-wrap gap-2">
                  {data.skills.map((s) => (
                    <li
                      key={s.skill_id}
                      className="text-xs px-2.5 py-1 rounded-md bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-200"
                    >
                      {s.name} · {s.proficiency_level}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-gray-500">No skills listed.</p>
              )}
            </section>
          </div>
        </>
      )}
    </RecruiterLayout>
  );
}
