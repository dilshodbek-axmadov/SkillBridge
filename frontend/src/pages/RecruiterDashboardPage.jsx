import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Search,
  Users,
  Bookmark,
  Briefcase,
  Sparkles,
  Lock,
  ArrowRight,
  Loader2,
  TrendingUp,
} from 'lucide-react';
import useRecruiterGate from '../hooks/useRecruiterGate';
import useAuthStore from '../store/authStore';
import RecruiterLayout from '../components/layout/RecruiterLayout';
import api from '../services/api';

function StatCard({ label, value, icon: Icon }) {
  return (
    <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-5 flex items-start gap-3 shadow-sm">
      <div className="w-10 h-10 rounded-lg bg-primary-50 dark:bg-primary-950 flex items-center justify-center flex-shrink-0">
        <Icon className="w-5 h-5 text-primary-600" />
      </div>
      <div>
        <p className="text-2xl font-bold text-gray-900 dark:text-gray-100 tabular-nums">{value}</p>
        <p className="text-xs text-gray-500 dark:text-gray-400">{label}</p>
      </div>
    </div>
  );
}

function QuickAction({ to, title, description, icon: Icon }) {
  return (
    <Link
      to={to}
      className="group flex gap-4 p-5 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 hover:border-primary-300 dark:hover:border-primary-600/40 hover:shadow-md transition-all no-underline"
    >
      <div className="w-11 h-11 rounded-xl bg-primary-50 dark:bg-primary-950 flex items-center justify-center flex-shrink-0 group-hover:bg-primary-100 dark:group-hover:bg-primary-900/50 transition-colors">
        <Icon className="w-5 h-5 text-primary-600" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">{title}</h3>
          <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-primary-600 flex-shrink-0 transition-colors" />
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 leading-relaxed">{description}</p>
      </div>
    </Link>
  );
}

export default function RecruiterDashboardPage() {
  const { user, fetchUser } = useRecruiterGate();
  const effectiveUser = useAuthStore((s) => s.user) || user;

  const [summary, setSummary] = useState(null);
  const [savedPreview, setSavedPreview] = useState([]);
  const [jobsPreview, setJobsPreview] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const run = async () => {
      try {
        let u = useAuthStore.getState().user;
        if (!u) await fetchUser();
        u = useAuthStore.getState().user;
        if (u?.user_type && u.user_type !== 'recruiter') {
          setLoading(false);
          return;
        }

        const [dashRes, savedRes, jobsRes] = await Promise.all([
          api.get('/recruiters/dashboard/'),
          api.get('/recruiters/saved-candidates/').catch(() => ({ data: { saved_candidates: [] } })),
          api.get('/recruiters/jobs/').catch(() => ({ data: { jobs: [] } })),
        ]);

        setSummary(dashRes.data);
        const saved = savedRes.data?.saved_candidates || [];
        setSavedPreview(saved.slice(0, 4));
        const jobs = jobsRes.data?.jobs || [];
        setJobsPreview(jobs.slice(0, 4));
      } catch (e) {
        if (e.response?.status === 401) {
          window.location.href = '/login?redirect=/recruiter/dashboard';
          return;
        }
        if (e.response?.status === 403) {
          setError('This area is only for recruiter accounts.');
        } else {
          setError('Could not load recruiter dashboard.');
        }
      } finally {
        setLoading(false);
      }
    };
    run();
  }, [fetchUser]);

  const firstName = effectiveUser?.first_name || effectiveUser?.email?.split('@')[0] || 'Recruiter';
  const plan = summary?.subscription?.plan || effectiveUser?.recruiter_plan || 'free';
  const isPro = summary?.subscription?.is_pro ?? effectiveUser?.recruiter_plan === 'pro';

  if (loading) {
    return (
      <RecruiterLayout user={effectiveUser}>
        <div className="flex items-center justify-center min-h-[50vh]">
          <Loader2 className="w-10 h-10 text-primary-600 animate-spin" />
        </div>
      </RecruiterLayout>
    );
  }

  if (error) {
    return (
      <RecruiterLayout user={effectiveUser}>
        <div className="rounded-xl border border-red-200 dark:border-red-900/50 bg-red-50 dark:bg-red-950/30 px-4 py-3 text-sm text-red-700 dark:text-red-300">
          {error}
        </div>
      </RecruiterLayout>
    );
  }

  const stats = summary?.stats;

  return (
    <RecruiterLayout user={effectiveUser}>
      {/* Welcome */}
      <div className="bg-gradient-to-r from-primary-600 via-primary-700 to-purple-600 rounded-2xl p-6 sm:p-8 text-white mb-8 shadow-lg">
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div>
            <p className="text-primary-100 text-sm font-medium mb-1">Recruiter workspace</p>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
              Welcome back, {firstName}
            </h1>
            <p className="text-white/85 mt-2 max-w-xl text-sm sm:text-base leading-relaxed">
              Search developers who opted in to recruiter visibility, save shortlists and searches, and manage your platform job postings in one place.
            </p>
          </div>
          <div className="flex flex-col items-start sm:items-end gap-2">
            <span
              className={`inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide px-3 py-1.5 rounded-full ${
                isPro ? 'bg-amber-400/25 text-amber-100' : 'bg-white/15 text-white'
              }`}
            >
              {isPro ? <Sparkles className="w-3.5 h-3.5" /> : <Lock className="w-3.5 h-3.5" />}
              {isPro ? 'Pro' : `${plan} plan`}
            </span>
            {!isPro && (
              <p className="text-xs text-white/75 max-w-[220px] sm:text-right">
                Upgrade to Pro to unlock full email and phone on candidate profiles.
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard label="Saved candidates" value={stats.candidates_saved} icon={Users} />
          <StatCard label="Saved searches" value={stats.saved_searches} icon={Bookmark} />
          <StatCard label="Jobs posted" value={stats.jobs_posted} icon={Briefcase} />
          <StatCard label="Active jobs" value={stats.active_jobs} icon={TrendingUp} />
        </div>
      )}

      {/* Quick actions */}
      <div className="mb-10">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Quick actions</h2>
        <div className="grid sm:grid-cols-2 gap-4">
          <QuickAction
            to="/recruiter/candidates"
            title="Find candidates"
            description="Filter by skills, location, and experience. Only developers open to recruiters appear in results."
            icon={Search}
          />
          <QuickAction
            to="/recruiter/jobs"
            title="Manage job posts"
            description="Create and edit SkillBridge job postings owned by your account."
            icon={Briefcase}
          />
          <QuickAction
            to="/recruiter/saved-candidates"
            title="Saved shortlist"
            description="Review candidates you have bookmarked and add notes."
            icon={Users}
          />
          <QuickAction
            to="/recruiter/saved-searches"
            title="Saved searches"
            description="Re-run stored filter sets without retyping criteria."
            icon={Bookmark}
          />
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Recent saved */}
        <section className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-5 sm:p-6">
          <div className="flex items-center justify-between gap-2 mb-4">
            <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">Recent saved candidates</h3>
            <Link
              to="/recruiter/saved-candidates"
              className="text-xs font-medium text-primary-600 hover:text-primary-700 no-underline"
            >
              View all
            </Link>
          </div>
          {savedPreview.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400 py-6 text-center">
              No saved candidates yet.{' '}
              <Link to="/recruiter/candidates" className="text-primary-600 font-medium no-underline">
                Start a search
              </Link>
            </p>
          ) : (
            <ul className="space-y-3">
              {savedPreview.map((row) => {
                const c = row.candidate;
                const name = c?.full_name || 'Candidate';
                return (
                  <li
                    key={row.saved_id}
                    className="flex items-center justify-between gap-3 py-2 border-b border-gray-100 dark:border-gray-800 last:border-0"
                  >
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">{name}</p>
                      <p className="text-xs text-gray-500 truncate">
                        {[c?.desired_role, c?.location].filter(Boolean).join(' · ') || '—'}
                      </p>
                    </div>
                    <Link
                      to={`/recruiter/candidates/${c?.id ?? ''}`}
                      className="text-xs text-primary-600 font-medium no-underline whitespace-nowrap"
                    >
                      Open
                    </Link>
                  </li>
                );
              })}
            </ul>
          )}
        </section>

        {/* Recent jobs */}
        <section className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-5 sm:p-6">
          <div className="flex items-center justify-between gap-2 mb-4">
            <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">Your recent job posts</h3>
            <Link to="/recruiter/jobs" className="text-xs font-medium text-primary-600 hover:text-primary-700 no-underline">
              View all
            </Link>
          </div>
          {jobsPreview.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400 py-6 text-center">
              No jobs yet.{' '}
              <Link to="/recruiter/jobs" className="text-primary-600 font-medium no-underline">
                Post a role
              </Link>
            </p>
          ) : (
            <ul className="space-y-3">
              {jobsPreview.map((job) => (
                <li
                  key={job.job_id}
                  className="flex items-center justify-between gap-3 py-2 border-b border-gray-100 dark:border-gray-800 last:border-0"
                >
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">{job.job_title}</p>
                    <p className="text-xs text-gray-500 truncate">
                      {[job.company_name, job.location].filter(Boolean).join(' · ') || '—'}
                      {job.is_active === false && (
                        <span className="ml-2 text-amber-600 dark:text-amber-400">Inactive</span>
                      )}
                    </p>
                  </div>
                  <Link
                    to={`/recruiter/jobs#job-${job.job_id}`}
                    className="text-xs text-primary-600 font-medium no-underline whitespace-nowrap"
                  >
                    Manage
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </RecruiterLayout>
  );
}
