import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Loader2,
  Lock,
  BarChart3,
  Users,
  Target,
  TrendingUp,
  Search,
  PieChart,
  Filter,
} from 'lucide-react';
import useAuthStore from '../store/authStore';
import useRecruiterGate from '../hooks/useRecruiterGate';
import RecruiterLayout from '../components/layout/RecruiterLayout';
import api from '../services/api';

function Section({ icon: Icon, title, description, children }) {
  return (
    <section className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-5 sm:p-6 mb-6">
      <div className="flex items-start gap-3 mb-4">
        <div className="w-10 h-10 rounded-lg bg-primary-50 dark:bg-primary-950 flex items-center justify-center flex-shrink-0">
          <Icon className="w-5 h-5 text-primary-600" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{title}</h2>
          {description ? (
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">{description}</p>
          ) : null}
        </div>
      </div>
      {children}
    </section>
  );
}

function BarRow({ label, value, max }) {
  const pct = max > 0 ? Math.min(100, Math.round((value / max) * 100)) : 0;
  return (
    <div className="mb-3 last:mb-0">
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-700 dark:text-gray-300 truncate pr-2" title={label}>
          {label}
        </span>
        <span className="text-gray-900 dark:text-gray-100 font-semibold tabular-nums">{value}</span>
      </div>
      <div className="h-2 rounded-full bg-gray-100 dark:bg-gray-800 overflow-hidden">
        <div
          className="h-full rounded-full bg-gradient-to-r from-primary-500 to-purple-500 transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function ProGate({ user }) {
  return (
    <RecruiterLayout user={user}>
      <div className="max-w-lg mx-auto text-center py-16 px-4">
        <div className="w-16 h-16 rounded-2xl bg-amber-50 dark:bg-amber-950/30 flex items-center justify-center mx-auto mb-6">
          <Lock className="w-8 h-8 text-amber-600" />
        </div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">Analytics — Pro only</h1>
        <p className="text-gray-600 dark:text-gray-400 text-sm leading-relaxed mb-8">
          The recruiter analytics dashboard includes market insights, search performance, response proxies, and hiring
          funnel metrics. Upgrade to <strong className="text-gray-800 dark:text-gray-200">SkillBridge Recruiter Pro</strong>{' '}
          to access this workspace.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            to="/settings"
            className="inline-flex items-center justify-center px-5 py-2.5 rounded-lg bg-primary-600 hover:bg-primary-700 text-white text-sm font-semibold no-underline"
          >
            Billing &amp; plan (coming soon)
          </Link>
          <Link
            to="/recruiter/dashboard"
            className="inline-flex items-center justify-center px-5 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-800 dark:text-gray-200 text-sm font-semibold no-underline"
          >
            Back to dashboard
          </Link>
        </div>
        <p className="text-xs text-gray-400 mt-8">
          Pro is enforced by your account&apos;s <code className="text-[11px]">recruiter_plan</code> on the server.
        </p>
      </div>
    </RecruiterLayout>
  );
}

export default function RecruiterAnalyticsPage() {
  useRecruiterGate();
  const user = useAuthStore((s) => s.user);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [proDenied, setProDenied] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const run = async () => {
      setLoading(true);
      setProDenied(false);
      setError('');
      try {
        const { data: d } = await api.get('/recruiters/analytics/');
        setData(d);
      } catch (e) {
        setData(null);
        if (e.response?.status === 403 && e.response?.data?.code === 'pro_required') {
          setProDenied(true);
        } else {
          setError(e.response?.data?.detail || e.response?.data?.error || 'Could not load analytics.');
        }
      } finally {
        setLoading(false);
      }
    };
    run();
  }, []);

  if (loading) {
    return (
      <RecruiterLayout user={user}>
        <div className="flex justify-center py-24">
          <Loader2 className="w-9 h-9 text-primary-600 animate-spin" />
        </div>
      </RecruiterLayout>
    );
  }

  if (proDenied) {
    return <ProGate user={user} />;
  }

  if (error) {
    return (
      <RecruiterLayout user={user}>
        <div className="rounded-xl border border-red-200 dark:border-red-900/50 bg-red-50 dark:bg-red-950/30 px-4 py-3 text-sm text-red-700 dark:text-red-300">
          {error}
        </div>
      </RecruiterLayout>
    );
  }

  if (!data) {
    return (
      <RecruiterLayout user={user}>
        <p className="text-sm text-gray-500">No data.</p>
      </RecruiterLayout>
    );
  }

  const market = data.market || {};
  const searchPerf = data.search_performance || {};
  const responseRates = data.response_rates || {};
  const funnel = data.hiring_funnel || {};

  const expRows = (market.by_experience_level || []).map((r) => ({
    label: r.profile__experience_level || '—',
    value: r.count,
  }));
  const expMax = Math.max(0, ...expRows.map((r) => r.value));

  const roleRows = (market.by_desired_role || []).slice(0, 10).map((r) => ({
    label: r.desired_role || '—',
    value: r.count,
  }));
  const roleMax = Math.max(0, ...roleRows.map((r) => r.value));

  const catRows = (market.by_skill_category || []).map((r) => ({
    label: r.category || '—',
    value: r.count,
  }));
  const catMax = Math.max(0, ...catRows.map((r) => r.value));

  const skillRows = (market.top_skills || []).slice(0, 12).map((r) => ({
    label: r.skill,
    value: r.count,
  }));
  const skillMax = Math.max(0, ...skillRows.map((r) => r.value));

  const trend = market.talent_pool_trend || [];
  const trendMax = Math.max(0, ...trend.map((r) => r.new_developers || 0));

  const funnelStages = funnel.stages || [];
  const funnelMax = Math.max(0, ...funnelStages.map((s) => s.value || 0));

  const weekly = searchPerf.weekly_shortlist_saves || [];
  const weeklyMax = Math.max(0, ...weekly.map((w) => w.saves || 0));

  return (
    <RecruiterLayout user={user}>
      <div className="mb-8">
        <div className="flex items-center gap-2 text-amber-700 dark:text-amber-400 text-xs font-semibold uppercase tracking-wide mb-2">
          <BarChart3 className="w-4 h-4" />
          Recruiter Pro
        </div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Analytics dashboard</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Market visibility across developers who opted in to recruiters, plus your shortlist and job performance.
        </p>
      </div>

      <Section
        icon={Users}
        title="Market insights"
        description="Developers with profiles open to recruiter visibility on the platform."
      >
        <p className="text-sm text-gray-600 dark:text-gray-300 mb-6">
          <strong className="text-gray-900 dark:text-gray-100 text-lg">{market.total_developers_open ?? 0}</strong>
          <span className="text-gray-500"> searchable talent profiles</span>
        </p>
        <div className="grid lg:grid-cols-2 gap-8">
          <div>
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">By experience level</h3>
            {expRows.length === 0 ? (
              <p className="text-sm text-gray-400">No data yet.</p>
            ) : (
              expRows.map((r) => <BarRow key={r.label} label={r.label} value={r.value} max={expMax} />)
            )}
          </div>
          <div>
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Top desired roles</h3>
            {roleRows.length === 0 ? (
              <p className="text-sm text-gray-400">No role labels yet.</p>
            ) : (
              roleRows.map((r) => <BarRow key={r.label} label={r.label} value={r.value} max={roleMax} />)
            )}
          </div>
          <div>
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">By skill category</h3>
            {catRows.length === 0 ? (
              <p className="text-sm text-gray-400">No categories yet.</p>
            ) : (
              catRows.map((r) => <BarRow key={r.label} label={r.label} value={r.value} max={catMax} />)
            )}
          </div>
          <div>
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Top skills</h3>
            {skillRows.length === 0 ? (
              <p className="text-sm text-gray-400">No skills yet.</p>
            ) : (
              skillRows.map((r) => <BarRow key={r.label} label={r.label} value={r.value} max={skillMax} />)
            )}
          </div>
        </div>
      </Section>

      <Section
        icon={TrendingUp}
        title="Talent pool trends"
        description="New developer accounts (opted in) by month, last 6 months."
      >
        {trend.length === 0 ? (
          <p className="text-sm text-gray-400">Not enough history.</p>
        ) : (
          trend.map((row) => (
            <BarRow key={row.period} label={row.period || '—'} value={row.new_developers || 0} max={trendMax} />
          ))
        )}
      </Section>

      <Section
        icon={Search}
        title="Search performance"
        description={searchPerf.description}
      >
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {[
            { label: 'Market index (open devs)', value: searchPerf.market_index_size },
            { label: 'Saves (30 days)', value: searchPerf.saves_last_30_days },
            { label: 'Shortlist (distinct)', value: searchPerf.shortlist_candidates_distinct },
            { label: 'Shortlist (total saves)', value: searchPerf.shortlist_saves_total },
          ].map((k) => (
            <div
              key={k.label}
              className="rounded-lg border border-gray-100 dark:border-gray-800 bg-gray-50/80 dark:bg-gray-800/40 p-4"
            >
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100 tabular-nums">{k.value ?? 0}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{k.label}</p>
            </div>
          ))}
        </div>
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Weekly shortlist activity</h3>
        {weekly.length === 0 ? (
          <p className="text-sm text-gray-400">Save candidates to see weekly trends.</p>
        ) : (
          weekly.map((w) => <BarRow key={w.week || String(w.saves)} label={w.week || '—'} value={w.saves || 0} max={weeklyMax} />)
        )}
      </Section>

      <Section
        icon={PieChart}
        title="Response rates"
        description={responseRates.description}
      >
        <div className="grid sm:grid-cols-3 gap-4">
          <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <p className="text-xs text-gray-500 uppercase font-medium">Apps / view</p>
            <p className="text-xl font-bold text-gray-900 dark:text-gray-100 mt-1 tabular-nums">
              {responseRates.applications_to_views_ratio != null
                ? responseRates.applications_to_views_ratio.toFixed(4)
                : '—'}
            </p>
          </div>
          <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <p className="text-xs text-gray-500 uppercase font-medium">Apps / active job</p>
            <p className="text-xl font-bold text-gray-900 dark:text-gray-100 mt-1 tabular-nums">
              {responseRates.applications_per_active_job != null
                ? responseRates.applications_per_active_job
                : '—'}
            </p>
          </div>
          <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <p className="text-xs text-gray-500 uppercase font-medium">Apps / shortlisted candidate</p>
            <p className="text-xl font-bold text-gray-900 dark:text-gray-100 mt-1 tabular-nums">
              {responseRates.applications_to_shortlisted_candidates_ratio != null
                ? responseRates.applications_to_shortlisted_candidates_ratio.toFixed(4)
                : '—'}
            </p>
          </div>
        </div>
      </Section>

      <Section
        icon={Filter}
        title="Hiring funnel"
        description={funnel.description}
      >
        <div className="flex flex-wrap gap-3 mb-6 text-sm text-gray-600 dark:text-gray-400">
          <span>
            <strong className="text-gray-900 dark:text-gray-100">{funnel.active_job_postings ?? 0}</strong> active
            postings
          </span>
          <span className="text-gray-300">·</span>
          <span>
            <strong className="text-gray-900 dark:text-gray-100">{funnel.total_job_postings ?? 0}</strong> total
            postings
          </span>
        </div>
        {funnelStages.length === 0 ? (
          <p className="text-sm text-gray-400">Publish a job to populate funnel metrics.</p>
        ) : (
          funnelStages.map((s) => (
            <BarRow key={s.id} label={s.label} value={s.value || 0} max={funnelMax} />
          ))
        )}
      </Section>

      <Section icon={Target} title="How to read this" description={null}>
        <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-2 list-disc pl-5">
          <li>Market blocks reflect the whole platform talent pool (opt-in), not only your shortlist.</li>
          <li>Search performance ties shortlist saves to your own discovery activity over time.</li>
          <li>Response rates approximate interest using job views and applications (outreach tracking can be added later).</li>
        </ul>
      </Section>
    </RecruiterLayout>
  );
}
