import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { Navigate } from 'react-router-dom';
import {
  RefreshCw, Play, RotateCcw, CheckCircle2, XCircle,
  Clock, Loader2, Database, Calendar, ServerCog,
  AlertTriangle, TrendingUp, ShieldAlert,
} from 'lucide-react';
import DashboardLayout from '../components/layout/DashboardLayout';
import AdminLayout from '../components/layout/AdminLayout';
import useAuthStore from '../store/authStore';
import api from '../services/api';

const STATUS_STYLES = {
  pending:  { bg: 'bg-amber-100 dark:bg-amber-900/30', text: 'text-amber-700 dark:text-amber-400', icon: Clock },
  running:  { bg: 'bg-blue-100 dark:bg-blue-900/30', text: 'text-blue-700 dark:text-blue-400', icon: Loader2 },
  success:  { bg: 'bg-emerald-100 dark:bg-emerald-900/30', text: 'text-emerald-700 dark:text-emerald-400', icon: CheckCircle2 },
  failed:   { bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-700 dark:text-red-400', icon: XCircle },
};

const TRIGGER_STYLES = {
  scheduled: { bg: 'bg-purple-100 dark:bg-purple-900/30', text: 'text-purple-700 dark:text-purple-400' },
  manual:    { bg: 'bg-blue-100 dark:bg-blue-900/30', text: 'text-blue-700 dark:text-blue-400' },
  startup:   { bg: 'bg-orange-100 dark:bg-orange-900/30', text: 'text-orange-700 dark:text-orange-400' },
};

function formatDuration(seconds) {
  if (!seconds && seconds !== 0) return '—';
  if (seconds < 60) return `${Math.round(seconds)}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`;
  return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
}

function formatDateTime(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  });
}

function StatusBadge({ status }) {
  const style = STATUS_STYLES[status] || STATUS_STYLES.pending;
  const Icon = style.icon;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${style.bg} ${style.text}`}>
      <Icon className={`w-3.5 h-3.5 ${status === 'running' ? 'animate-spin' : ''}`} />
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}

function TriggerBadge({ trigger }) {
  const style = TRIGGER_STYLES[trigger] || TRIGGER_STYLES.scheduled;
  return (
    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide ${style.bg} ${style.text}`}>
      {trigger}
    </span>
  );
}

function StatsRow({ stats, t }) {
  if (!stats) return null;
  const successRate = stats.total_runs > 0
    ? Math.round((stats.successful_runs / stats.total_runs) * 100)
    : 0;

  const items = [
    {
      icon: <Database className="w-5 h-5 text-blue-600 dark:text-blue-400" />,
      bg: 'bg-blue-100 dark:bg-blue-900/30',
      value: stats.total_jobs_in_db?.toLocaleString() || '0',
      label: t('backgroundTasks.stats.totalJobs'),
    },
    {
      icon: <TrendingUp className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />,
      bg: 'bg-emerald-100 dark:bg-emerald-900/30',
      value: stats.jobs_created_last_7_days?.toLocaleString() || '0',
      label: t('backgroundTasks.stats.recentJobs'),
    },
    {
      icon: <CheckCircle2 className="w-5 h-5 text-purple-600 dark:text-purple-400" />,
      bg: 'bg-purple-100 dark:bg-purple-900/30',
      value: `${successRate}%`,
      label: t('backgroundTasks.stats.successRate'),
    },
    {
      icon: <Calendar className="w-5 h-5 text-orange-600 dark:text-orange-400" />,
      bg: 'bg-orange-100 dark:bg-orange-900/30',
      value: stats.last_success_date || '—',
      label: t('backgroundTasks.stats.lastRun'),
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
      {items.map((s, i) => (
        <div key={i} className="bg-white dark:bg-gray-900 rounded-xl border border-gray-100 dark:border-gray-800 p-4 flex items-center gap-3">
          <div className={`w-10 h-10 ${s.bg} rounded-lg flex items-center justify-center flex-shrink-0`}>
            {s.icon}
          </div>
          <div className="min-w-0">
            <p className="text-xl font-bold text-gray-900 dark:text-gray-100 truncate">{s.value}</p>
            <p className="text-xs text-gray-400 dark:text-gray-500">{s.label}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

function RunDetailModal({ run, onClose, onRetry, retrying }) {
  if (!run) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-2xl w-full max-w-lg max-h-[85vh] overflow-y-auto z-10">
        <div className="sticky top-0 bg-white dark:bg-gray-900 border-b border-gray-100 dark:border-gray-800 px-6 py-4 flex items-start justify-between gap-4 z-10">
          <div>
            <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">
              Extraction Run — {run.run_date}
            </h2>
            <p className="text-xs text-gray-400 mt-0.5">Source: {run.source}</p>
          </div>
          <button onClick={onClose} className="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 bg-transparent border-none cursor-pointer">
            <XCircle className="w-5 h-5" />
          </button>
        </div>

        <div className="px-6 py-5 space-y-4">
          <div className="flex items-center gap-3">
            <StatusBadge status={run.status} />
            <TriggerBadge trigger={run.trigger} />
          </div>

          <div className="grid grid-cols-2 gap-3">
            {[
              { label: 'Started', value: formatDateTime(run.started_at) },
              { label: 'Finished', value: formatDateTime(run.finished_at) },
              { label: 'Duration', value: formatDuration(run.duration_seconds) },
              { label: 'Jobs Created', value: run.jobs_created },
              { label: 'Jobs Updated', value: run.jobs_updated },
              { label: 'Jobs Skipped', value: run.jobs_skipped },
              { label: 'Jobs Deactivated', value: run.jobs_deactivated },
              { label: 'Aliases Created', value: run.aliases_created },
              { label: 'Errors', value: run.errors_count },
            ].map((item, i) => (
              <div key={i} className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
                <p className="text-xs text-gray-400 dark:text-gray-500 mb-0.5">{item.label}</p>
                <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">{item.value}</p>
              </div>
            ))}
          </div>

          {run.error_message && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-1">
                <AlertTriangle className="w-4 h-4 text-red-500" />
                <p className="text-sm font-semibold text-red-700 dark:text-red-400">Error Details</p>
              </div>
              <pre className="text-xs text-red-600 dark:text-red-300 whitespace-pre-wrap break-words mt-1 font-mono">
                {run.error_message}
              </pre>
            </div>
          )}

          {run.celery_task_id && (
            <div className="text-xs text-gray-400 dark:text-gray-500">
              Task ID: <span className="font-mono">{run.celery_task_id}</span>
            </div>
          )}

          {run.status === 'failed' && (
            <button
              onClick={() => onRetry(run.id)}
              disabled={retrying}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-semibold transition-colors disabled:opacity-50 border-none cursor-pointer"
            >
              {retrying ? <Loader2 className="w-4 h-4 animate-spin" /> : <RotateCcw className="w-4 h-4" />}
              {retrying ? 'Retrying...' : 'Retry Extraction'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default function BackgroundTasksPage({ variant = 'developer' }) {
  const { t } = useTranslation();
  const { user, fetchUser } = useAuthStore();
  const Layout = variant === 'admin' ? AdminLayout : DashboardLayout;
  const [stats, setStats] = useState(null);
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);
  const [retryingId, setRetryingId] = useState(null);
  const [selectedRun, setSelectedRun] = useState(null);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  useEffect(() => { fetchUser(); }, []);

  const fetchData = useCallback(async () => {
    try {
      const params = {};
      if (statusFilter) params.status = statusFilter;

      const [statsRes, runsRes] = await Promise.all([
        api.get('/jobs/extraction-stats/'),
        api.get('/jobs/extraction-runs/', { params }),
      ]);
      setStats(statsRes.data);
      setRuns(runsRes.data.runs || []);
      setError('');
    } catch (err) {
      if (err.response?.status === 403) {
        setError(t('backgroundTasks.accessDenied'));
      } else {
        setError('Failed to load extraction data.');
      }
    } finally {
      setLoading(false);
    }
  }, [statusFilter, t]);

  useEffect(() => { fetchData(); }, [fetchData]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleTrigger = async () => {
    setTriggering(true);
    try {
      await api.post('/jobs/extraction-runs/trigger/');
      await fetchData();
    } catch (err) {
      if (err.response?.status === 409) {
        // Already exists — just refresh
        await fetchData();
      }
    } finally {
      setTriggering(false);
    }
  };

  const handleRetry = async (runId) => {
    setRetryingId(runId);
    try {
      await api.post(`/jobs/extraction-runs/${runId}/retry/`);
      await fetchData();
      setSelectedRun(null);
    } catch {
      // ignore
    } finally {
      setRetryingId(null);
    }
  };

  // Guard: must be authenticated
  if (!user) {
    return (
      <Layout user={user}>
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 text-primary-600 animate-spin" />
        </div>
      </Layout>
    );
  }

  // Guard: admin only
  if (!user.is_staff && !user.is_superuser) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <Layout user={user}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-indigo-100 to-purple-200 dark:from-indigo-900/40 dark:to-purple-900/40 rounded-xl flex items-center justify-center">
              <ServerCog className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {t('backgroundTasks.title')}
              </h1>
              <p className="text-sm text-gray-400 dark:text-gray-500">
                {t('backgroundTasks.subtitle')}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={fetchData}
              className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-600 dark:text-gray-300 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors cursor-pointer"
            >
              <RefreshCw className="w-4 h-4" />
              {t('backgroundTasks.refresh') || 'Refresh'}
            </button>
            <button
              onClick={handleTrigger}
              disabled={triggering}
              className="flex items-center gap-2 px-4 py-2 text-sm font-semibold text-white bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors disabled:opacity-50 border-none cursor-pointer"
            >
              {triggering ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
              {t('backgroundTasks.runNow')}
            </button>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4 flex items-center gap-3">
            <ShieldAlert className="w-5 h-5 text-red-500 flex-shrink-0" />
            <p className="text-sm text-red-700 dark:text-red-400">{error}</p>
          </div>
        )}

        {/* Stats */}
        <StatsRow stats={stats} t={t} />

        {/* Filter Tabs */}
        <div className="flex items-center gap-2 flex-wrap">
          {['', 'success', 'failed', 'running', 'pending'].map((f) => (
            <button
              key={f}
              onClick={() => setStatusFilter(f)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors border-none cursor-pointer ${
                statusFilter === f
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
              }`}
            >
              {f === '' ? t('backgroundTasks.filterAll') || 'All' : f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>

        {/* Loading */}
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="w-8 h-8 text-primary-600 animate-spin" />
          </div>
        ) : runs.length === 0 ? (
          /* Empty state */
          <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 p-12 text-center">
            <ServerCog className="w-10 h-10 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
            <p className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
              {t('backgroundTasks.noRuns')}
            </p>
            <p className="text-xs text-gray-400 dark:text-gray-500">
              Click "Run Now" to trigger your first extraction.
            </p>
          </div>
        ) : (
          /* Runs Table */
          <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 overflow-hidden">
            {/* Desktop table */}
            <div className="hidden md:block overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-100 dark:border-gray-800">
                    {[
                      t('backgroundTasks.table.date'),
                      t('backgroundTasks.table.status'),
                      t('backgroundTasks.table.trigger'),
                      t('backgroundTasks.table.duration'),
                      t('backgroundTasks.table.jobsCreated'),
                      t('backgroundTasks.table.jobsUpdated'),
                      t('backgroundTasks.table.deactivated'),
                      t('backgroundTasks.table.errors'),
                      t('backgroundTasks.table.actions'),
                    ].map((h, i) => (
                      <th key={i} className="px-4 py-3 text-left text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50 dark:divide-gray-800">
                  {runs.map((run) => (
                    <tr
                      key={run.id}
                      onClick={() => setSelectedRun(run)}
                      className="hover:bg-gray-50 dark:hover:bg-gray-800/50 cursor-pointer transition-colors"
                    >
                      <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-gray-100 whitespace-nowrap">
                        {run.run_date}
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge status={run.status} />
                      </td>
                      <td className="px-4 py-3">
                        <TriggerBadge trigger={run.trigger} />
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300 whitespace-nowrap">
                        {formatDuration(run.duration_seconds)}
                      </td>
                      <td className="px-4 py-3 text-sm font-semibold text-emerald-600 dark:text-emerald-400">
                        {run.jobs_created > 0 ? `+${run.jobs_created}` : run.jobs_created}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">
                        {run.jobs_updated}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        {run.jobs_deactivated > 0 ? (
                          <span className="text-orange-600 dark:text-orange-400 font-semibold">{run.jobs_deactivated}</span>
                        ) : (
                          <span className="text-gray-400">0</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        {run.errors_count > 0 ? (
                          <span className="text-red-600 dark:text-red-400 font-semibold">{run.errors_count}</span>
                        ) : (
                          <span className="text-gray-400">0</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {run.status === 'failed' && (
                          <button
                            onClick={(e) => { e.stopPropagation(); handleRetry(run.id); }}
                            disabled={retryingId === run.id}
                            className="flex items-center gap-1.5 px-3 py-1.5 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg text-xs font-semibold hover:bg-red-100 dark:hover:bg-red-900/40 transition-colors border-none cursor-pointer disabled:opacity-50"
                          >
                            {retryingId === run.id ? (
                              <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            ) : (
                              <RotateCcw className="w-3.5 h-3.5" />
                            )}
                            {t('backgroundTasks.retry')}
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mobile cards */}
            <div className="md:hidden divide-y divide-gray-100 dark:divide-gray-800">
              {runs.map((run) => (
                <div
                  key={run.id}
                  onClick={() => setSelectedRun(run)}
                  className="p-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 cursor-pointer transition-colors"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-semibold text-gray-900 dark:text-gray-100">{run.run_date}</span>
                    <StatusBadge status={run.status} />
                  </div>
                  <div className="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
                    <TriggerBadge trigger={run.trigger} />
                    <span>{formatDuration(run.duration_seconds)}</span>
                    <span className="text-emerald-600 dark:text-emerald-400 font-semibold">+{run.jobs_created}</span>
                  </div>
                  {run.status === 'failed' && (
                    <button
                      onClick={(e) => { e.stopPropagation(); handleRetry(run.id); }}
                      disabled={retryingId === run.id}
                      className="mt-2 flex items-center gap-1.5 px-3 py-1.5 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg text-xs font-semibold border-none cursor-pointer"
                    >
                      <RotateCcw className="w-3.5 h-3.5" />
                      {t('backgroundTasks.retry')}
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Detail Modal */}
      <RunDetailModal
        run={selectedRun}
        onClose={() => setSelectedRun(null)}
        onRetry={handleRetry}
        retrying={retryingId === selectedRun?.id}
      />
    </Layout>
  );
}
