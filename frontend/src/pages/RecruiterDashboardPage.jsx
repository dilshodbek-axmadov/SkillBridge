import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Search,
  Users,
  BarChart3,
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
  const { t } = useTranslation();
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
          setError(t('recruiter.recruiterOnly'));
        } else {
          setError(t('recruiter.couldNotLoadDashboard'));
        }
      } finally {
        setLoading(false);
      }
    };
    run();
  }, [fetchUser, t]);

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
            <p className="text-primary-100 text-sm font-medium mb-1">{t('recruiter.workspace')}</p>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
              {t('recruiter.welcomeBack')}, {firstName}
            </h1>
            <p className="text-white/85 mt-2 max-w-xl text-sm sm:text-base leading-relaxed">
              {t('recruiter.welcomeDesc')}
            </p>
          </div>
          <div className="flex flex-col items-start sm:items-end gap-2">
            <span
              className={`inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide px-3 py-1.5 rounded-full ${
                isPro ? 'bg-amber-400/25 text-amber-100' : 'bg-white/15 text-white'
              }`}
            >
              {isPro ? <Sparkles className="w-3.5 h-3.5" /> : <Lock className="w-3.5 h-3.5" />}
              {isPro ? t('recruiter.pro') : `${plan} ${t('recruiter.plan')}`}
            </span>
            {!isPro && (
              <p className="text-xs text-white/75 max-w-[220px] sm:text-right">
                {t('recruiter.upgradeToUnlock')}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid sm:grid-cols-3 gap-4 mb-8">
          <StatCard label={t('recruiter.savedCandidates')} value={stats.candidates_saved} icon={Users} />
          <StatCard label={t('recruiter.jobsPosted')} value={stats.jobs_posted} icon={Briefcase} />
          <StatCard label={t('recruiter.activeJobs')} value={stats.active_jobs} icon={TrendingUp} />
        </div>
      )}

      {/* Quick actions */}
      <div className="mb-10">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">{t('recruiter.quickActions')}</h2>
        <div className="grid sm:grid-cols-2 gap-4">
          <QuickAction
            to="/recruiter/candidates"
            title={t('recruiter.findCandidates')}
            description={t('recruiter.findCandidatesDesc')}
            icon={Search}
          />
          <QuickAction
            to="/recruiter/jobs"
            title={t('recruiter.manageJobPosts')}
            description={t('recruiter.manageJobPostsDesc')}
            icon={Briefcase}
          />
          <QuickAction
            to="/recruiter/saved-candidates"
            title={t('recruiter.savedShortlist')}
            description={t('recruiter.savedShortlistDesc')}
            icon={Users}
          />
          <QuickAction
            to="/recruiter/analytics"
            title={t('recruiter.analyticsPro')}
            description={t('recruiter.analyticsProDesc')}
            icon={BarChart3}
          />
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Recent saved */}
        <section className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-5 sm:p-6">
          <div className="flex items-center justify-between gap-2 mb-4">
            <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">{t('recruiter.recentSavedCandidates')}</h3>
            <Link
              to="/recruiter/saved-candidates"
              className="text-xs font-medium text-primary-600 hover:text-primary-700 no-underline"
            >
              {t('recruiter.viewAll')}
            </Link>
          </div>
          {savedPreview.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400 py-6 text-center">
              {t('recruiter.noSavedCandidatesYet')}{' '}
              <Link to="/recruiter/candidates" className="text-primary-600 font-medium no-underline">
                {t('recruiter.startSearch')}
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
                      {t('recruiter.open')}
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
            <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">{t('recruiter.recentJobPosts')}</h3>
            <Link to="/recruiter/jobs" className="text-xs font-medium text-primary-600 hover:text-primary-700 no-underline">
              {t('recruiter.viewAll')}
            </Link>
          </div>
          {jobsPreview.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400 py-6 text-center">
              {t('recruiter.noJobsYet')}{' '}
              <Link to="/recruiter/jobs" className="text-primary-600 font-medium no-underline">
                {t('recruiter.postRole')}
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
                        <span className="ml-2 text-amber-600 dark:text-amber-400">{t('recruiter.inactive')}</span>
                      )}
                    </p>
                  </div>
                  <Link
                    to={`/recruiter/jobs#job-${job.job_id}`}
                    className="text-xs text-primary-600 font-medium no-underline whitespace-nowrap"
                  >
                    {t('recruiter.manage')}
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
