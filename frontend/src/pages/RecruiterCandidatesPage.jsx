import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Search, Loader2, UserPlus, Check } from 'lucide-react';
import useAuthStore from '../store/authStore';
import useRecruiterGate from '../hooks/useRecruiterGate';
import RecruiterLayout from '../components/layout/RecruiterLayout';
import api from '../services/api';

export default function RecruiterCandidatesPage() {
  useRecruiterGate();
  const user = useAuthStore((s) => s.user);
  const [searchParams] = useSearchParams();

  const [q, setQ] = useState('');
  const [location, setLocation] = useState('');
  const [skill, setSkill] = useState('');
  const [candidates, setCandidates] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [savingId, setSavingId] = useState(null);

  const load = async (overrides) => {
    const qv = overrides?.q ?? q;
    const lv = overrides?.location ?? location;
    const sv = overrides?.skill ?? skill;
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (qv.trim()) params.set('q', qv.trim());
      if (lv.trim()) params.set('location', lv.trim());
      if (sv.trim()) params.set('skill', sv.trim());
      const qs = params.toString();
      const path = qs ? `/recruiters/candidates/?${qs}` : '/recruiters/candidates/';
      const { data } = await api.get(path);
      setCandidates(data.candidates || []);
      setTotal(data.total ?? 0);
    } catch {
      setCandidates([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const qv = searchParams.get('q') || '';
    const lv = searchParams.get('location') || '';
    const sv = searchParams.get('skill') || '';
    setQ(qv);
    setLocation(lv);
    setSkill(sv);
    load({ q: qv, location: lv, skill: sv });
    // eslint-disable-next-line react-hooks/exhaustive-deps -- sync URL → filter + fetch
  }, [searchParams]);

  const handleSearch = (e) => {
    e.preventDefault();
    load();
  };

  const saveCandidate = async (candidateId, alreadySaved) => {
    if (alreadySaved) return;
    setSavingId(candidateId);
    try {
      await api.post('/recruiters/saved-candidates/', { candidate_id: candidateId });
      setCandidates((rows) =>
        rows.map((c) => (c.id === candidateId ? { ...c, is_saved: true } : c))
      );
    } catch {
      /* toast optional */
    } finally {
      setSavingId(null);
    }
  };

  return (
    <RecruiterLayout user={user}>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Find candidates</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Developers who marked their profile open to recruiters. Refine by name, role keywords, location, or skill.
        </p>
      </div>

      <form onSubmit={handleSearch} className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4 sm:p-5 mb-6 space-y-4">
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <input
            type="search"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Name, role, keyword…"
            className="w-full px-3 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-gray-100"
          />
          <input
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="Location"
            className="w-full px-3 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-gray-100"
          />
          <input
            type="text"
            value={skill}
            onChange={(e) => setSkill(e.target.value)}
            placeholder="Skill (e.g. React)"
            className="w-full px-3 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-gray-100"
          />
          <button
            type="submit"
            className="inline-flex items-center justify-center gap-2 h-[42px] rounded-lg bg-primary-600 hover:bg-primary-700 text-white text-sm font-semibold border-none cursor-pointer"
          >
            <Search className="w-4 h-4" />
            Search
          </button>
        </div>
        {!loading && (
          <p className="text-xs text-gray-500 dark:text-gray-400">
            {total} {total === 1 ? 'profile' : 'profiles'} match
          </p>
        )}
      </form>

      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="w-8 h-8 text-primary-600 animate-spin" />
        </div>
      ) : candidates.length === 0 ? (
        <div className="text-center py-16 text-gray-500 dark:text-gray-400 text-sm border border-dashed border-gray-200 dark:border-gray-800 rounded-xl">
          No candidates match your filters. Try broader keywords or clear a filter.
        </div>
      ) : (
        <ul className="space-y-3">
          {candidates.map((c) => (
            <li
              key={c.id}
              className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
            >
              <div className="min-w-0 flex-1">
                <Link
                  to={`/recruiter/candidates/${c.id}`}
                  className="text-base font-semibold text-gray-900 dark:text-gray-100 hover:text-primary-600 no-underline"
                >
                  {c.full_name || 'Developer'}
                </Link>
                <p className="text-sm text-gray-600 dark:text-gray-300 mt-0.5">
                  {[c.desired_role || c.current_job_position, c.experience_level, c.location]
                    .filter(Boolean)
                    .join(' · ')}
                </p>
                {c.top_skills?.length > 0 && (
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                    {c.top_skills.slice(0, 6).join(' · ')}
                  </p>
                )}
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                {c.is_saved ? (
                  <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-600 dark:text-emerald-400 px-3 py-2 rounded-lg bg-emerald-50 dark:bg-emerald-950/40">
                    <Check className="w-3.5 h-3.5" />
                    Saved
                  </span>
                ) : (
                  <button
                    type="button"
                    disabled={savingId === c.id}
                    onClick={() => saveCandidate(c.id, c.is_saved)}
                    className="inline-flex items-center gap-1.5 text-xs font-semibold text-primary-600 bg-primary-50 dark:bg-primary-950/50 hover:bg-primary-100 dark:hover:bg-primary-900/40 px-3 py-2 rounded-lg border-none cursor-pointer disabled:opacity-50"
                  >
                    <UserPlus className="w-3.5 h-3.5" />
                    {savingId === c.id ? 'Saving…' : 'Save'}
                  </button>
                )}
                <Link
                  to={`/recruiter/candidates/${c.id}`}
                  className="text-xs font-semibold text-gray-700 dark:text-gray-200 px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 no-underline"
                >
                  Profile
                </Link>
              </div>
            </li>
          ))}
        </ul>
      )}
    </RecruiterLayout>
  );
}
