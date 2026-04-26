import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  Loader2,
  Lock,
  UserPlus,
  Check,
  MapPin,
  Star,
  Send,
  Download,
  ShieldCheck,
  Github,
  Linkedin,
  ExternalLink,
  FileDown,
} from 'lucide-react';
import useAuthStore from '../store/authStore';
import useRecruiterGate from '../hooks/useRecruiterGate';
import RecruiterLayout from '../components/layout/RecruiterLayout';
import api from '../services/api';
import { startProCheckout } from '../utils/startProCheckout';

function cn(...parts) {
  return parts.filter(Boolean).join(' ');
}

function maskEmail(email) {
  if (!email || typeof email !== 'string' || !email.includes('@')) return '—';
  const [name, domain] = email.split('@');
  const safeName = name.length <= 2 ? `${name[0] || '*'}*` : `${name.slice(0, 1)}${'*'.repeat(Math.min(6, name.length - 2))}${name.slice(-1)}`;
  const safeDomain =
    domain.length <= 3 ? `${domain[0] || '*'}**` : `${domain.slice(0, 1)}${'*'.repeat(Math.min(6, domain.length - 2))}${domain.slice(-1)}`;
  return `${safeName}@${safeDomain}`;
}

function maskPhone(phone) {
  if (!phone || typeof phone !== 'string') return '—';
  const digits = phone.replace(/[^\d+]/g, '');
  if (digits.length < 6) return '—';
  return `${digits.slice(0, 4)} ${'*'.repeat(2)} ${'*'.repeat(3)} ${'*'.repeat(4)}`;
}

function proficiencyToPercent(level) {
  const v = String(level || '').toLowerCase();
  if (v.includes('expert')) return 95;
  if (v.includes('advanced')) return 80;
  if (v.includes('intermediate')) return 60;
  if (v.includes('beginner')) return 35;
  return 50;
}

function proficiencyColor(level) {
  const v = String(level || '').toLowerCase();
  if (v.includes('expert')) return 'bg-emerald-600';
  if (v.includes('advanced')) return 'bg-sky-600';
  if (v.includes('intermediate')) return 'bg-amber-500';
  if (v.includes('beginner')) return 'bg-gray-400';
  return 'bg-gray-500';
}

const BIO_PREVIEW_CHARS = 180;

function truncateBio(text, max = BIO_PREVIEW_CHARS) {
  if (!text) return '';
  const trimmed = String(text).trim();
  if (trimmed.length <= max) return trimmed;
  // Prefer cutting at end of a sentence within the limit; fall back to last space.
  const slice = trimmed.slice(0, max);
  const lastSentence = Math.max(slice.lastIndexOf('. '), slice.lastIndexOf('! '), slice.lastIndexOf('? '));
  let cut = lastSentence > 60 ? lastSentence + 1 : slice.lastIndexOf(' ');
  if (cut < 60) cut = max;
  return trimmed.slice(0, cut).trimEnd();
}

function BioBlock({ text }) {
  const isLong = (text || '').length > BIO_PREVIEW_CHARS;
  const preview = useMemo(() => truncateBio(text), [text]);
  return (
    <p className="mt-4 text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
      {isLong ? `${preview}…` : text}
    </p>
  );
}

function pickDefaultCvId(cvs) {
  if (!Array.isArray(cvs) || cvs.length === 0) return null;
  const def = cvs.find((c) => c?.is_default);
  return (def || cvs[0])?.cv_id ?? null;
}

function parseFilenameFromContentDisposition(headerValue) {
  if (!headerValue) return null;
  const m = /filename=\"?([^\";]+)\"?/i.exec(headerValue);
  return m?.[1] ?? null;
}

export default function RecruiterCandidateDetailPage() {
  useRecruiterGate();
  const { candidateId } = useParams();
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [upgrading, setUpgrading] = useState(false);

  const handleUpgrade = async () => {
    if (upgrading) return;
    setUpgrading(true);
    setError('');
    const ok = await startProCheckout({ onError: (msg) => setError(msg) });
    if (!ok) setUpgrading(false);
  };

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

  const downloadCv = async () => {
    if (!data?.id) return;
    setDownloading(true);
    try {
      const cvId = pickDefaultCvId(data?.cvs);
      const qp = new URLSearchParams();
      qp.set('export_format', 'pdf');

      if (!cvId) {
        setError('This candidate has no CV to download.');
        return;
      }

      const res = await api.get(`/cv/${cvId}/export/?${qp.toString()}`, {
        responseType: 'blob',
      });
      const blob = new Blob([res.data], { type: res.headers?.['content-type'] || 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      const suggested =
        parseFilenameFromContentDisposition(res.headers?.['content-disposition']) || `${data.full_name || 'candidate'}_CV.pdf`;
      a.href = url;
      a.download = suggested;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      if (e?.response?.status === 403) setError('CV download is available on Recruiter Pro.');
      else if (e?.response?.status === 404) setError('This candidate has no CV to download.');
      else setError('Could not download CV.');
    } finally {
      setDownloading(false);
    }
  };

  const profile = data?.profile || {};
  const contactLocked = !data?.contact_unlocked;
  const recruiterIsPro = !!(user?.is_staff || String(user?.recruiter_plan || '').toLowerCase() === 'pro');
  const yearsTotal = Array.isArray(data?.skills)
    ? Math.round(data.skills.reduce((sum, s) => sum + (Number(s?.years_of_experience) || 0), 0) * 10) / 10
    : 0;
  const defaultCvId = pickDefaultCvId(data?.cvs);
  const heroTitle = profile.current_job_position || profile.desired_role || 'Developer';
  const initials = String(data?.full_name || 'U')
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase())
    .join('');
  const groupedSkills = (Array.isArray(data?.skills) ? data.skills : []).reduce((acc, s) => {
    const cat = s?.category || 'Other';
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(s);
    return acc;
  }, {});

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
        <div className="max-w-[1000px] mx-auto">
          <div className="flex flex-col lg:flex-row gap-6">
            <div className="flex-1 min-w-0">
              {/* Header */}
              <section className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6">
                <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
                  <div className="flex items-start gap-4 min-w-0">
                    <div className="w-[120px] h-[120px] rounded-full bg-gradient-to-br from-primary-600 to-purple-500 flex items-center justify-center text-white text-3xl font-bold flex-shrink-0">
                      {initials || 'U'}
                    </div>
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-gray-100 truncate">
                          {data.full_name}
                        </h1>
                        <span className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-900/40">
                          <ShieldCheck className="w-4 h-4" />
                          {profile.open_to_recruiters ? 'Open to offers' : 'Not looking'}
                        </span>
                        {yearsTotal > 0 && (
                          <span className="inline-flex items-center text-xs font-semibold px-2.5 py-1 rounded-full bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-200 border border-gray-200 dark:border-gray-700">
                            {yearsTotal} yrs exp
                          </span>
                        )}
                      </div>
                      <p className="text-gray-700 dark:text-gray-200 mt-1 font-medium">{heroTitle}</p>
                      <div className="mt-2 flex flex-wrap items-center gap-3 text-sm text-gray-600 dark:text-gray-300">
                        {profile.location && (
                          <span className="inline-flex items-center gap-1.5">
                            <MapPin className="w-4 h-4" />
                            {profile.location}
                          </span>
                        )}
                        {profile.experience_level && <span>{profile.experience_level}</span>}
                      </div>
                      {profile.bio && <BioBlock text={profile.bio} />}
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    {saved ? (
                      <span className="inline-flex items-center gap-1 text-sm font-semibold text-emerald-700 dark:text-emerald-300 px-4 py-2 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900/40">
                        <Check className="w-4 h-4" />
                        Saved
                      </span>
                    ) : (
                      <button
                        type="button"
                        onClick={saveCandidate}
                        disabled={saving}
                        className="inline-flex items-center gap-2 text-sm font-semibold text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-900 hover:bg-gray-50 dark:hover:bg-gray-800 px-4 py-2 rounded-lg border border-gray-200 dark:border-gray-700 cursor-pointer disabled:opacity-60"
                      >
                        <Star className="w-4 h-4" />
                        {saving ? 'Saving…' : 'Save Candidate'}
                      </button>
                    )}

                    <button
                      type="button"
                      disabled={!recruiterIsPro}
                      onClick={async () => {
                        try {
                          const { data: out } = await api.post('/messages/threads/', {
                            recipient_id: data.id,
                            body: 'Hi! I’m interested in your profile.',
                          });
                          const threadId = out?.thread?.thread_id;
                          if (threadId) navigate(`/messages?thread=${threadId}`);
                          else navigate('/messages');
                        } catch {
                          setError('Could not start a conversation.');
                        }
                      }}
                      className={cn(
                        'inline-flex items-center gap-2 text-sm font-semibold px-4 py-2 rounded-lg border-none cursor-pointer',
                        recruiterIsPro
                          ? 'text-white bg-primary-600 hover:bg-primary-700'
                          : 'text-gray-500 bg-gray-100 dark:bg-gray-800 cursor-not-allowed'
                      )}
                      title={recruiterIsPro ? '' : 'Pro only'}
                    >
                      <Send className="w-4 h-4" />
                      Send Message
                      {!recruiterIsPro && <span className="text-xs font-semibold ml-1">(Pro)</span>}
                    </button>

                    <button
                      type="button"
                      disabled={!recruiterIsPro || !defaultCvId || downloading}
                      onClick={downloadCv}
                      className={cn(
                        'inline-flex items-center gap-2 text-sm font-semibold px-4 py-2 rounded-lg border-none cursor-pointer',
                        recruiterIsPro && defaultCvId
                          ? 'text-white bg-purple-600 hover:bg-purple-700'
                          : 'text-gray-500 bg-gray-100 dark:bg-gray-800 cursor-not-allowed'
                      )}
                      title={!defaultCvId ? 'No CV available' : recruiterIsPro ? '' : 'Pro only'}
                    >
                      {downloading ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileDown className="w-4 h-4" />}
                      Download CV
                      {!recruiterIsPro && <span className="text-xs font-semibold ml-1">(Pro)</span>}
                    </button>
                  </div>
                </div>
              </section>

              {/* Contact card */}
              <section className="mt-6 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 relative overflow-hidden">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Contact Information</h2>

                <div className={cn('space-y-3', contactLocked && 'blur-sm select-none pointer-events-none')}>
                  <div className="flex items-center justify-between gap-4 text-sm">
                    <span className="text-gray-500">Email</span>
                    <span className="text-gray-900 dark:text-gray-100 break-all">
                      {data.email ? (
                        <a className="text-primary-600 hover:text-primary-700 no-underline" href={`mailto:${data.email}`}>
                          {data.email}
                        </a>
                      ) : (
                        '—'
                      )}
                    </span>
                  </div>
                  <div className="flex items-center justify-between gap-4 text-sm">
                    <span className="text-gray-500">Phone</span>
                    <span className="text-gray-900 dark:text-gray-100">
                      {data.phone ? <a className="text-primary-600 no-underline" href={`tel:${data.phone}`}>{data.phone}</a> : '—'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between gap-4 text-sm">
                    <span className="text-gray-500">LinkedIn</span>
                    <span className="text-gray-900 dark:text-gray-100">
                      {profile.linkedin_url ? (
                        <a className="inline-flex items-center gap-1 text-primary-600 hover:text-primary-700 no-underline" href={profile.linkedin_url} target="_blank" rel="noreferrer">
                          <Linkedin className="w-4 h-4" />
                          Open
                          <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                      ) : (
                        '—'
                      )}
                    </span>
                  </div>
                  <div className="flex items-center justify-between gap-4 text-sm">
                    <span className="text-gray-500">GitHub</span>
                    <span className="text-gray-900 dark:text-gray-100">
                      {profile.github_url ? (
                        <a className="inline-flex items-center gap-1 text-primary-600 hover:text-primary-700 no-underline" href={profile.github_url} target="_blank" rel="noreferrer">
                          <Github className="w-4 h-4" />
                          Open
                          <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                      ) : (
                        '—'
                      )}
                    </span>
                  </div>
                </div>

                {contactLocked && (
                  <div className="absolute inset-0 flex items-center justify-center p-6">
                    <div className="w-full max-w-md rounded-2xl border border-purple-200 dark:border-purple-900/40 bg-white/90 dark:bg-gray-950/80 backdrop-blur px-5 py-4">
                      <div className="flex items-start gap-3">
                        <div className="w-10 h-10 rounded-xl bg-purple-600 flex items-center justify-center flex-shrink-0">
                          <Lock className="w-5 h-5 text-white" />
                        </div>
                        <div className="min-w-0">
                          <p className="font-semibold text-gray-900 dark:text-gray-100">Unlock contact details</p>
                          <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                            Free plan shows masked contact info. Upgrade to Pro to view full email and phone.
                          </p>
                          <div className="mt-3 flex flex-wrap gap-2">
                            <span className="text-sm text-gray-700 dark:text-gray-200">
                              {maskEmail(profile?.email || data?.email)}
                            </span>
                            <span className="text-sm text-gray-700 dark:text-gray-200">
                              {maskPhone(data?.phone)}
                            </span>
                          </div>
                          <button
                            type="button"
                            onClick={handleUpgrade}
                            disabled={upgrading}
                            className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-white bg-purple-600 hover:bg-purple-700 disabled:opacity-60 disabled:cursor-not-allowed px-4 py-2 rounded-lg border-none cursor-pointer"
                          >
                            {upgrading ? (
                              <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                              <ShieldCheck className="w-4 h-4" />
                            )}
                            {upgrading ? 'Redirecting…' : 'Upgrade Now'}
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </section>

              {/* Skills */}
              <section className="mt-6 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Technical Skills</h2>
                {Object.keys(groupedSkills).length ? (
                  <div className="space-y-5">
                    {Object.entries(groupedSkills).map(([category, skills]) => (
                      <div key={category}>
                        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-3">{category}</h3>
                        <div className="grid sm:grid-cols-2 gap-3">
                          {skills.map((s) => {
                            const pct = proficiencyToPercent(s?.proficiency_level);
                            return (
                              <div
                                key={s.skill_id}
                                className="rounded-xl border border-gray-200 dark:border-gray-800 p-4 bg-white dark:bg-gray-950/30"
                              >
                                <div className="flex items-start justify-between gap-3">
                                  <div className="min-w-0">
                                    <p className="text-sm font-semibold text-gray-900 dark:text-gray-100 truncate">
                                      {s?.name || 'Skill'}
                                    </p>
                                    <p className="text-xs text-gray-500 mt-0.5">
                                      {s?.years_of_experience ? `${s.years_of_experience} yrs` : '—'} · {s?.proficiency_level || '—'}
                                    </p>
                                  </div>
                                  {s?.is_primary && (
                                    <span className="text-xs font-semibold px-2 py-1 rounded-full bg-primary-50 dark:bg-primary-950/30 text-primary-700 dark:text-primary-300 border border-primary-200 dark:border-primary-900/40 flex-shrink-0">
                                      Core
                                    </span>
                                  )}
                                </div>
                                <div className="mt-3 h-2 rounded-full bg-gray-100 dark:bg-gray-800 overflow-hidden">
                                  <div className={cn('h-full rounded-full', proficiencyColor(s?.proficiency_level))} style={{ width: `${pct}%` }} />
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">No skills listed.</p>
                )}
              </section>

              {/* Projects */}
              <section className="mt-6 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Projects & Portfolio</h2>
                {Array.isArray(data?.portfolio_projects) && data.portfolio_projects.length ? (
                  <div className="grid sm:grid-cols-2 gap-4">
                    {data.portfolio_projects.slice(0, 6).map((p) => (
                      <div key={p.project_id} className="rounded-2xl border border-gray-200 dark:border-gray-800 p-5">
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0">
                            <p className="text-sm font-semibold text-gray-900 dark:text-gray-100 truncate">{p.title}</p>
                            <p className="text-xs text-gray-500 mt-0.5">{p.target_role || 'Project'}</p>
                          </div>
                          <span className="text-xs font-semibold px-2 py-1 rounded-full bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-900/40">
                            Completed
                          </span>
                        </div>
                        <div className="mt-4 flex flex-wrap gap-3 text-sm">
                          {p.github_url && (
                            <a className="inline-flex items-center gap-1 text-primary-600 hover:text-primary-700 no-underline" href={p.github_url} target="_blank" rel="noreferrer">
                              <Github className="w-4 h-4" />
                              GitHub
                              <ExternalLink className="w-3.5 h-3.5" />
                            </a>
                          )}
                          {p.live_demo_url && (
                            <a className="inline-flex items-center gap-1 text-primary-600 hover:text-primary-700 no-underline" href={p.live_demo_url} target="_blank" rel="noreferrer">
                              <ExternalLink className="w-4 h-4" />
                              Live
                            </a>
                          )}
                        </div>
                        {p.completed_at && (
                          <p className="mt-3 text-xs text-gray-500">
                            Completed: {new Date(p.completed_at).toLocaleDateString()}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">No projects added yet.</p>
                )}
              </section>
            </div>

            {/* Sidebar */}
            <aside className="lg:w-[320px] flex-shrink-0">
              <div className="lg:sticky lg:top-6 space-y-4">
                <section className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-5">
                  <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">Quick actions</h3>
                  <div className="space-y-2">
                    <button
                      type="button"
                      onClick={saveCandidate}
                      disabled={saving || saved}
                      className="w-full inline-flex items-center justify-center gap-2 text-sm font-semibold text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-900 hover:bg-gray-50 dark:hover:bg-gray-800 px-4 py-2 rounded-lg border border-gray-200 dark:border-gray-700 disabled:opacity-60"
                    >
                      <Star className="w-4 h-4" />
                      {saved ? 'Saved' : saving ? 'Saving…' : 'Save Candidate'}
                    </button>
                    <button
                      type="button"
                      onClick={downloadCv}
                      disabled={!recruiterIsPro || !defaultCvId || downloading}
                      className={cn(
                        'w-full inline-flex items-center justify-center gap-2 text-sm font-semibold px-4 py-2 rounded-lg border-none',
                        recruiterIsPro && defaultCvId ? 'text-white bg-purple-600 hover:bg-purple-700' : 'text-gray-500 bg-gray-100 dark:bg-gray-800'
                      )}
                    >
                      {downloading ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileDown className="w-4 h-4" />}
                      Download CV (PDF)
                    </button>
                    <button
                      type="button"
                      disabled
                      className="w-full inline-flex items-center justify-center gap-2 text-sm font-semibold text-gray-500 bg-gray-100 dark:bg-gray-800 px-4 py-2 rounded-lg border-none cursor-not-allowed"
                      title="Coming soon"
                    >
                      <Send className="w-4 h-4" />
                      Schedule Interview
                    </button>
                  </div>
                  {!recruiterIsPro && (
                    <p className="mt-3 text-xs text-gray-500">
                      Pro features are highlighted in <span className="font-semibold text-purple-600">purple</span>.
                    </p>
                  )}
                </section>
              </div>
            </aside>
          </div>
        </div>
      )}
    </RecruiterLayout>
  );
}
