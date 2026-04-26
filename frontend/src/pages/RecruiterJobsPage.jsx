import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Loader2,
  Plus,
  Pencil,
  Eye,
  Users,
  BarChart2,
  Briefcase,
  Archive,
  Send,
  FileEdit,
  Lock,
  Sparkles,
} from 'lucide-react';
import useAuthStore from '../store/authStore';
import useRecruiterGate from '../hooks/useRecruiterGate';
import useRecruiterAccess from '../hooks/useRecruiterAccess';
import RecruiterLayout from '../components/layout/RecruiterLayout';
import api from '../services/api';
import { startProCheckout } from '../utils/startProCheckout';

function PerfCard({ label, value, icon: Icon, sub }) {
  return (
    <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4 flex gap-3 shadow-sm">
      <div className="w-10 h-10 rounded-lg bg-primary-50 dark:bg-primary-950 flex items-center justify-center flex-shrink-0">
        <Icon className="w-5 h-5 text-primary-600" />
      </div>
      <div>
        <p className="text-2xl font-bold text-gray-900 dark:text-gray-100 tabular-nums">{value}</p>
        <p className="text-xs font-medium text-gray-500 dark:text-gray-400">{label}</p>
        {sub ? <p className="text-[11px] text-gray-400 mt-0.5">{sub}</p> : null}
      </div>
    </div>
  );
}

export default function RecruiterJobsPage() {
  const { t } = useTranslation();
  useRecruiterGate();
  const user = useAuthStore((s) => s.user);
  const { access, refresh: refreshAccess } = useRecruiterAccess();

  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('active');
  const [actionId, setActionId] = useState(null);

  const TABS = [
    { id: 'active', label: t('recruiter.active') },
    { id: 'draft', label: t('recruiter.drafts') },
    { id: 'archived', label: t('recruiter.archived') },
  ];

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await api.get('/recruiters/jobs/');
      setJobs(data.jobs || []);
    } catch {
      setJobs([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const filtered = useMemo(() => {
    return jobs.filter((j) => {
      const s = j.listing_status || (j.is_active ? 'active' : 'archived');
      if (tab === 'active') return s === 'active';
      if (tab === 'draft') return s === 'draft';
      return s === 'archived';
    });
  }, [jobs, tab]);

  const performance = useMemo(() => {
    const activeJobs = jobs.filter((j) => (j.listing_status || (j.is_active ? 'active' : 'archived')) === 'active');
    const views = activeJobs.reduce((a, j) => a + (Number(j.view_count) || 0), 0);
    const apps = activeJobs.reduce((a, j) => a + (Number(j.application_count) || 0), 0);
    return {
      activeCount: activeJobs.length,
      totalViews: views,
      totalApplications: apps,
    };
  }, [jobs]);

  const patchJob = async (jobId, body) => {
    setActionId(jobId);
    try {
      await api.patch(`/recruiters/jobs/${jobId}/`, body);
      await load();
      refreshAccess();
    } catch {
      /* store toast */
    } finally {
      setActionId(null);
    }
  };

  const jobsAccess = access?.jobs;
  const canPost = jobsAccess ? jobsAccess.allowed : true;
  const isFree = access ? !access.is_pro : false;
  const [upgradeBusy, setUpgradeBusy] = useState(false);
  const [upgradeError, setUpgradeError] = useState('');

  const handleUpgrade = async () => {
    setUpgradeError('');
    setUpgradeBusy(true);
    const ok = await startProCheckout({ onError: setUpgradeError });
    if (!ok) setUpgradeBusy(false);
  };
  const tooltip = !canPost
    ? jobsAccess?.reason || t('recruiter.freePlanLimitReached')
    : isFree && jobsAccess?.limit != null
      ? t('recruiter.freePlanUsage', {
          used: jobsAccess.used,
          limit: jobsAccess.limit,
          plural: jobsAccess.limit === 1 ? '' : 's',
          days: jobsAccess.window_days
        })
      : '';

  return (
    <RecruiterLayout user={user}>
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{t('recruiter.myJobPostings')}</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {t('recruiter.myJobPostingsDesc')}
          </p>
        </div>
        {canPost ? (
          <Link
            to="/recruiter/jobs/new"
            title={tooltip}
            className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-primary-600 hover:bg-primary-700 text-white text-sm font-semibold no-underline shrink-0"
          >
            <Plus className="w-4 h-4" />
            {t('recruiter.createJob')}
          </Link>
        ) : (
          <button
            type="button"
            disabled
            title={tooltip}
            aria-disabled="true"
            className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-gray-200 dark:bg-gray-800 text-gray-500 text-sm font-semibold border-none cursor-not-allowed shrink-0"
          >
            <Lock className="w-4 h-4" />
            {t('recruiter.createJob')}
          </button>
        )}
      </div>

      {isFree && jobsAccess?.limit != null && (
        <div
          className={`mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 rounded-xl border px-4 py-3 text-sm ${
            canPost
              ? 'border-amber-200 dark:border-amber-900/50 bg-amber-50 dark:bg-amber-950/30 text-amber-900 dark:text-amber-200'
              : 'border-red-200 dark:border-red-900/50 bg-red-50 dark:bg-red-950/30 text-red-800 dark:text-red-300'
          }`}
        >
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 shrink-0" />
            <span>
              {t('recruiter.freePlanInfo', {
                used: jobsAccess.used,
                limit: jobsAccess.limit,
                plural: jobsAccess.limit === 1 ? '' : 's',
                days: jobsAccess.window_days
              })}{' '}
              {canPost
                ? t('recruiter.canPostOneMore')
                : t('recruiter.reachedFreeLimit')}
            </span>
          </div>
          <button
            type="button"
            onClick={handleUpgrade}
            disabled={upgradeBusy}
            className="inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary-600 hover:bg-primary-700 disabled:opacity-60 text-white text-xs font-semibold border-none cursor-pointer shrink-0"
          >
            {upgradeBusy ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                {t('recruiter.redirecting')}
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5" />
                {t('recruiter.upgradeToPro')}
              </>
            )}
          </button>
        </div>
      )}
      {upgradeError && (
        <div className="mb-4 text-sm text-red-700 dark:text-red-300 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900/50 rounded-lg px-3 py-2">
          {upgradeError}
        </div>
      )}

      {/* Job performance */}
      <section className="mb-8">
        <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3 flex items-center gap-2">
          <BarChart2 className="w-4 h-4 text-primary-600" />
          {t('recruiter.jobPerformance')}
        </h2>
        <div className="grid sm:grid-cols-3 gap-4">
          <PerfCard
            label={t('recruiter.profileViews')}
            value={loading ? '—' : performance.totalViews.toLocaleString()}
            icon={Eye}
            sub={t('recruiter.profileViewsSub')}
          />
          <PerfCard
            label={t('recruiter.applications')}
            value={loading ? '—' : performance.totalApplications.toLocaleString()}
            icon={Users}
            sub={t('recruiter.applicationsSub')}
          />
          <PerfCard
            label={t('recruiter.activeJobsCount')}
            value={loading ? '—' : performance.activeCount}
            icon={Briefcase}
            sub={t('recruiter.activeJobsSub')}
          />
        </div>
      </section>

      {/* Tabs */}
      <div className="flex flex-wrap gap-2 mb-4 border-b border-gray-200 dark:border-gray-800 pb-1">
        {TABS.map((t) => {
          const active = tab === t.id;
          return (
            <button
              key={t.id}
              type="button"
              onClick={() => setTab(t.id)}
              className={`px-4 py-2 text-sm font-semibold rounded-t-lg border-b-2 -mb-px transition-colors cursor-pointer bg-transparent ${
                active
                  ? 'border-primary-600 text-primary-700 dark:text-primary-400'
                  : 'border-transparent text-gray-500 hover:text-gray-800 dark:hover:text-gray-200'
              }`}
            >
              {t.label}
              {!loading && (
                <span className="ml-1.5 text-xs font-normal opacity-70">
                  (
                  {t.id === 'active'
                    ? jobs.filter((j) => (j.listing_status || (j.is_active ? 'active' : 'archived')) === 'active').length
                    : t.id === 'draft'
                      ? jobs.filter((j) => (j.listing_status || '') === 'draft').length
                      : jobs.filter((j) => (j.listing_status || '') === 'archived').length}
                  )
                </span>
              )}
            </button>
          );
        })}
      </div>

      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="w-8 h-8 text-primary-600 animate-spin" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16 text-gray-500 dark:text-gray-400 text-sm border border-dashed border-gray-200 dark:border-gray-800 rounded-xl">
          {tab === 'draft' && (
            <>
              {t('recruiter.noDraftsYet')}{' '}
              <Link to="/recruiter/jobs/new" className="text-primary-600 font-medium no-underline">
                {t('recruiter.createJobAndSave')}
              </Link>{' '}
              {t('recruiter.saveAsDraft')}
            </>
          )}
          {tab === 'active' && (
            <>
              {t('recruiter.noActivePostings')}{' '}
              <Link to="/recruiter/jobs/new" className="text-primary-600 font-medium no-underline">
                {t('recruiter.createOne')}
              </Link>
              .
            </>
          )}
          {tab === 'archived' && t('recruiter.noArchivedJobs')}
        </div>
      ) : (
        <ul className="space-y-3">
          {filtered.map((job) => {
            const busy = actionId === job.job_id;
            const status = job.listing_status || (job.is_active ? 'active' : 'archived');
            return (
              <li
                key={job.job_id}
                id={`job-${job.job_id}`}
                className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4 sm:p-5 scroll-mt-24"
              >
                <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100">{job.job_title}</h2>
                      <span
                        className={`text-[10px] uppercase tracking-wide font-bold px-2 py-0.5 rounded ${
                          status === 'active'
                            ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-300'
                            : status === 'draft'
                              ? 'bg-amber-100 text-amber-900 dark:bg-amber-950/40 dark:text-amber-200'
                              : 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'
                        }`}
                      >
                        {status}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-300 mt-0.5">
                      {[job.company_name, job.location, job.employment_type?.replace('_', ' ')].filter(Boolean).join(' · ')}
                    </p>
                    <div className="flex flex-wrap gap-4 mt-3 text-xs text-gray-500 dark:text-gray-400">
                      <span className="inline-flex items-center gap-1">
                        <Eye className="w-3.5 h-3.5" />
                        {Number(job.view_count) || 0} {t('recruiter.views')}
                      </span>
                      <span className="inline-flex items-center gap-1">
                        <Users className="w-3.5 h-3.5" />
                        {Number(job.application_count) || 0} {t('recruiter.applications')}
                      </span>
                    </div>
                    {job.job_description && (
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-3 line-clamp-2">{job.job_description}</p>
                    )}
                  </div>

                  <div className="flex flex-wrap gap-2 lg:flex-col lg:items-stretch lg:min-w-[160px]">
                    <Link
                      to={`/recruiter/jobs/${job.job_id}/edit`}
                      className="inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-primary-50 dark:bg-primary-950/40 text-primary-700 dark:text-primary-300 text-xs font-semibold no-underline hover:bg-primary-100 dark:hover:bg-primary-900/30"
                    >
                      <Pencil className="w-3.5 h-3.5" />
                      {t('recruiter.edit')}
                    </Link>
                    {status === 'draft' && (
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() => patchJob(job.job_id, { listing_status: 'active' })}
                        className="inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg border border-emerald-300 dark:border-emerald-800 text-emerald-700 dark:text-emerald-400 text-xs font-semibold bg-transparent cursor-pointer disabled:opacity-50"
                      >
                        <Send className="w-3.5 h-3.5" />
                        {t('recruiter.publish')}
                      </button>
                    )}
                    {status === 'active' && (
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() => patchJob(job.job_id, { listing_status: 'archived' })}
                        className="inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 text-xs font-semibold bg-transparent cursor-pointer disabled:opacity-50"
                      >
                        <Archive className="w-3.5 h-3.5" />
                        {t('recruiter.archive')}
                      </button>
                    )}
                    {status === 'archived' && (
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() => patchJob(job.job_id, { listing_status: 'draft' })}
                        className="inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg border border-amber-300 dark:border-amber-800 text-amber-800 dark:text-amber-300 text-xs font-semibold bg-transparent cursor-pointer disabled:opacity-50"
                      >
                        <FileEdit className="w-3.5 h-3.5" />
                        {t('recruiter.restoreToDraft')}
                      </button>
                    )}
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </RecruiterLayout>
  );
}
