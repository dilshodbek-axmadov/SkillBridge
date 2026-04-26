import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import {
  Loader2,
  Lock,
  Sparkles,
  Users,
  Briefcase,
  TrendingUp,
  MapPin,
  Target,
  Brain,
  AlertTriangle,
  ArrowUpRight,
  Eye,
  Send,
  Trophy,
  Calendar,
  Layers,
} from 'lucide-react';
import useRecruiterGate from '../hooks/useRecruiterGate';
import useAuthStore from '../store/authStore';
import RecruiterLayout from '../components/layout/RecruiterLayout';
import api from '../services/api';

/* ============================== utilities ============================== */

const PALETTE = [
  '#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981',
  '#06b6d4', '#3b82f6', '#ef4444', '#84cc16', '#a855f7',
  '#f97316', '#14b8a6',
];

const fmt = (n) => {
  if (n === null || n === undefined) return '—';
  if (typeof n !== 'number') return n;
  if (Math.abs(n) >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (Math.abs(n) >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toLocaleString();
};

const fmtPct = (n) => (n == null ? '—' : `${Number(n).toFixed(1)}%`);

const fmtRate = (rate) => (rate == null ? '—' : `${(rate * 100).toFixed(2)}%`);

/* ============================== chart blocks ============================== */

function ChartCard({ icon: Icon, title, subtitle, children, right }) {
  return (
    <section className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-5 sm:p-6 shadow-sm">
      <div className="flex items-start justify-between gap-3 mb-4">
        <div className="flex items-start gap-3 min-w-0">
          {Icon && (
            <div className="w-9 h-9 rounded-lg bg-primary-50 dark:bg-primary-950 flex items-center justify-center flex-shrink-0">
              <Icon className="w-4.5 h-4.5 text-primary-600" />
            </div>
          )}
          <div className="min-w-0">
            <h3 className="text-sm sm:text-base font-semibold text-gray-900 dark:text-gray-100 truncate">{title}</h3>
            {subtitle && <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{subtitle}</p>}
          </div>
        </div>
        {right}
      </div>
      {children}
    </section>
  );
}

function HBars({ data, valueKey = 'count', labelKey = 'label', maxBars = 10, renderTooltip, formatValue = fmt }) {
  const { t } = useTranslation();
  const items = (data || []).slice(0, maxBars);
  const max = items.reduce((m, it) => Math.max(m, Number(it[valueKey]) || 0), 0) || 1;
  const [hover, setHover] = useState(null);

  if (items.length === 0) {
    return <p className="text-sm text-gray-500 py-6 text-center">{t('recruiter.analytics.noData')}</p>;
  }

  return (
    <div className="space-y-2.5">
      {items.map((it, i) => {
        const v = Number(it[valueKey]) || 0;
        const w = (v / max) * 100;
        const color = PALETTE[i % PALETTE.length];
        const isHover = hover === i;
        return (
          <div
            key={`${it[labelKey]}-${i}`}
            className="relative"
            onMouseEnter={() => setHover(i)}
            onMouseLeave={() => setHover(null)}
          >
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="font-medium text-gray-700 dark:text-gray-300 truncate pr-2">{it[labelKey]}</span>
              <span className="text-gray-500 dark:text-gray-400 tabular-nums">{formatValue(v)}</span>
            </div>
            <div className="h-2.5 rounded-full bg-gray-100 dark:bg-gray-800 overflow-hidden">
              <div
                className="h-full rounded-full transition-all"
                style={{
                  width: `${w}%`,
                  background: `linear-gradient(90deg, ${color}, ${color}dd)`,
                  boxShadow: isHover ? `0 0 0 2px ${color}33` : 'none',
                }}
              />
            </div>
            {isHover && renderTooltip && (
              <div className="absolute z-10 -top-2 right-0 translate-y-[-100%] bg-gray-900 text-white text-xs rounded-md px-3 py-2 shadow-xl pointer-events-none whitespace-nowrap">
                {renderTooltip(it)}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function VBars({ data, valueKey = 'count', labelKey = 'label', renderTooltip, formatValue = fmt, height = 180 }) {
  const { t } = useTranslation();
  const items = data || [];
  const max = items.reduce((m, it) => Math.max(m, Number(it[valueKey]) || 0), 0) || 1;
  const [hover, setHover] = useState(null);

  if (items.length === 0) {
    return <p className="text-sm text-gray-500 py-6 text-center">{t('recruiter.analytics.noData')}</p>;
  }

  return (
    <div>
      <div className="flex items-end gap-2" style={{ height }}>
        {items.map((it, i) => {
          const v = Number(it[valueKey]) || 0;
          const h = max ? (v / max) * (height - 30) : 0;
          const color = PALETTE[i % PALETTE.length];
          const isHover = hover === i;
          return (
            <div
              key={`${it[labelKey]}-${i}`}
              className="relative flex-1 flex flex-col items-center justify-end group cursor-default"
              onMouseEnter={() => setHover(i)}
              onMouseLeave={() => setHover(null)}
            >
              {isHover && renderTooltip && (
                <div className="absolute -top-1 left-1/2 -translate-x-1/2 -translate-y-full bg-gray-900 text-white text-xs rounded-md px-3 py-2 shadow-xl pointer-events-none whitespace-nowrap z-10">
                  {renderTooltip(it)}
                </div>
              )}
              <span className="text-[10px] text-gray-500 mb-1 tabular-nums">{formatValue(v)}</span>
              <div
                className="w-full rounded-t-md transition-all"
                style={{
                  height: `${h}px`,
                  background: `linear-gradient(180deg, ${color}, ${color}aa)`,
                  boxShadow: isHover ? `0 -2px 12px ${color}66` : 'none',
                  minHeight: v > 0 ? 4 : 0,
                }}
              />
            </div>
          );
        })}
      </div>
      <div className="flex gap-2 mt-2">
        {items.map((it, i) => (
          <div key={i} className="flex-1 text-[10px] text-center text-gray-500 dark:text-gray-400 truncate" title={it[labelKey]}>
            {it[labelKey]}
          </div>
        ))}
      </div>
    </div>
  );
}

function Donut({ data, valueKey = 'count', labelKey = 'label', size = 200 }) {
  const { t } = useTranslation();
  const items = data || [];
  const total = items.reduce((s, it) => s + (Number(it[valueKey]) || 0), 0);
  const [hover, setHover] = useState(null);

  if (total <= 0) {
    return <p className="text-sm text-gray-500 py-6 text-center">{t('recruiter.analytics.noData')}</p>;
  }

  const cx = size / 2;
  const cy = size / 2;
  const r = size / 2 - 12;
  const stroke = 22;
  let cumulative = 0;

  const arcs = items.map((it, i) => {
    const v = Number(it[valueKey]) || 0;
    const frac = v / total;
    const start = cumulative;
    cumulative += frac;
    const end = cumulative;
    const angleStart = start * 2 * Math.PI - Math.PI / 2;
    const angleEnd = end * 2 * Math.PI - Math.PI / 2;
    const x1 = cx + r * Math.cos(angleStart);
    const y1 = cy + r * Math.sin(angleStart);
    const x2 = cx + r * Math.cos(angleEnd);
    const y2 = cy + r * Math.sin(angleEnd);
    const largeArc = end - start > 0.5 ? 1 : 0;
    const d = `M ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2}`;
    return { d, color: PALETTE[i % PALETTE.length], it, frac, idx: i };
  });

  const hovered = hover != null ? items[hover] : null;

  return (
    <div className="flex flex-col sm:flex-row items-center gap-6">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size}>
          <circle cx={cx} cy={cy} r={r} fill="none" stroke="rgba(0,0,0,0.05)" strokeWidth={stroke} />
          {arcs.map((a) => (
            <path
              key={a.idx}
              d={a.d}
              fill="none"
              stroke={a.color}
              strokeWidth={hover === a.idx ? stroke + 6 : stroke}
              strokeLinecap="butt"
              style={{ transition: 'stroke-width 150ms', cursor: 'pointer' }}
              onMouseEnter={() => setHover(a.idx)}
              onMouseLeave={() => setHover(null)}
            />
          ))}
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          {hovered ? (
            <>
              <span className="text-xs text-gray-500">{hovered[labelKey]}</span>
              <span className="text-2xl font-bold text-gray-900 dark:text-gray-100 tabular-nums">
                {fmt(Number(hovered[valueKey]))}
              </span>
              <span className="text-xs text-gray-500">
                {((Number(hovered[valueKey]) / total) * 100).toFixed(1)}%
              </span>
            </>
          ) : (
            <>
              <span className="text-xs text-gray-500">{t('recruiter.analytics.total')}</span>
              <span className="text-2xl font-bold text-gray-900 dark:text-gray-100 tabular-nums">{fmt(total)}</span>
            </>
          )}
        </div>
      </div>
      <ul className="flex-1 space-y-1.5 w-full">
        {items.map((it, i) => {
          const v = Number(it[valueKey]) || 0;
          const pct = ((v / total) * 100).toFixed(1);
          return (
            <li
              key={i}
              className={`flex items-center justify-between gap-3 text-xs px-2 py-1 rounded-md cursor-default transition-colors ${
                hover === i ? 'bg-gray-100 dark:bg-gray-800' : ''
              }`}
              onMouseEnter={() => setHover(i)}
              onMouseLeave={() => setHover(null)}
            >
              <div className="flex items-center gap-2 min-w-0">
                <span
                  className="w-3 h-3 rounded-full flex-shrink-0"
                  style={{ backgroundColor: PALETTE[i % PALETTE.length] }}
                />
                <span className="truncate text-gray-700 dark:text-gray-300">{it[labelKey]}</span>
              </div>
              <span className="text-gray-500 tabular-nums">
                {fmt(v)} <span className="text-gray-400">· {pct}%</span>
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

function HeatmapBlocks({ items, valueKey = 'count', labelKey = 'location' }) {
  const { t } = useTranslation();
  const max = (items || []).reduce((m, it) => Math.max(m, Number(it[valueKey]) || 0), 0) || 1;
  const [hover, setHover] = useState(null);

  if (!items || items.length === 0) {
    return <p className="text-sm text-gray-500 py-6 text-center">{t('recruiter.analytics.noLocationData')}</p>;
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
      {items.map((it, i) => {
        const v = Number(it[valueKey]) || 0;
        const intensity = v / max;
        const bg = `rgba(99, 102, 241, ${0.15 + intensity * 0.7})`;
        return (
          <div
            key={`${it[labelKey]}-${i}`}
            className="relative rounded-lg p-3 cursor-default border border-gray-100 dark:border-gray-800 transition-transform hover:scale-[1.03]"
            style={{ background: bg }}
            onMouseEnter={() => setHover(i)}
            onMouseLeave={() => setHover(null)}
          >
            <div className="flex items-center gap-1.5 text-xs font-medium text-gray-900 dark:text-white">
              <MapPin className="w-3 h-3" />
              <span className="truncate">{it[labelKey]}</span>
            </div>
            <p className="text-lg font-bold text-gray-900 dark:text-white tabular-nums mt-1">{fmt(v)}</p>
            <p className="text-[10px] text-gray-700 dark:text-gray-200">{fmtPct(it.percentage)}</p>
            {hover === i && (
              <div className="absolute z-10 -top-2 left-1/2 -translate-x-1/2 -translate-y-full bg-gray-900 text-white text-xs rounded-md px-3 py-2 shadow-xl whitespace-nowrap">
                {it[labelKey]}: <b>{fmt(v)}</b> candidates ({fmtPct(it.percentage)})
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function GroupedBars({ rows }) {
  const { t } = useTranslation();
  // rows: [{ role, market_avg, market_min, market_max, job_count }]
  const items = rows || [];
  const max = items.reduce((m, it) => Math.max(m, Number(it.market_max || it.market_avg || 0)), 0) || 1;
  const [hover, setHover] = useState(null);

  if (items.length === 0) {
    return <p className="text-sm text-gray-500 py-6 text-center">{t('recruiter.analytics.noSalaryData')}</p>;
  }

  return (
    <div className="space-y-3">
      {items.map((it, i) => {
        const minW = ((Number(it.market_min) || 0) / max) * 100;
        const maxW = ((Number(it.market_max) || 0) / max) * 100;
        const avgW = ((Number(it.market_avg) || 0) / max) * 100;
        const color = PALETTE[i % PALETTE.length];
        return (
          <div
            key={i}
            className="relative"
            onMouseEnter={() => setHover(i)}
            onMouseLeave={() => setHover(null)}
          >
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="font-medium text-gray-700 dark:text-gray-300 truncate pr-2">{it.role}</span>
              <span className="text-gray-500 dark:text-gray-400 tabular-nums">
                {fmt(it.market_avg)} <span className="text-gray-400">avg</span>
              </span>
            </div>
            <div className="relative h-3 rounded-full bg-gray-100 dark:bg-gray-800 overflow-hidden">
              <div
                className="absolute h-full opacity-25"
                style={{ width: `${maxW}%`, background: color }}
              />
              <div
                className="absolute h-full opacity-50"
                style={{ width: `${avgW}%`, background: color }}
              />
              <div
                className="absolute h-full"
                style={{ width: `${minW}%`, background: color, opacity: 0.85 }}
              />
            </div>
            {hover === i && (
              <div className="absolute z-10 right-0 -top-2 -translate-y-full bg-gray-900 text-white text-xs rounded-md px-3 py-2 shadow-xl whitespace-nowrap">
                <div><b>{it.role}</b></div>
                <div>Market min: {fmt(it.market_min)}</div>
                <div>Market avg: {fmt(it.market_avg)}</div>
                <div>Market max: {fmt(it.market_max)}</div>
                <div>Sample: {fmt(it.job_count)} postings</div>
                <div className="text-gray-300 mt-1">
                  Candidate expectation:{' '}
                  {it.candidate_expectation == null ? 'not collected' : fmt(it.candidate_expectation)}
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

/* ============================== KPI row ============================== */

function KpiCard({ icon: Icon, label, value, hint, accent = 'primary' }) {
  const accents = {
    primary: 'bg-primary-50 dark:bg-primary-950 text-primary-600',
    green: 'bg-emerald-50 dark:bg-emerald-950 text-emerald-600',
    amber: 'bg-amber-50 dark:bg-amber-950 text-amber-600',
    pink: 'bg-pink-50 dark:bg-pink-950 text-pink-600',
  };
  return (
    <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4 shadow-sm">
      <div className="flex items-start gap-3">
        <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${accents[accent]}`}>
          <Icon className="w-4.5 h-4.5" />
        </div>
        <div className="min-w-0">
          <p className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100 tabular-nums">{value}</p>
          <p className="text-xs text-gray-500 dark:text-gray-400">{label}</p>
          {hint && <p className="text-[11px] text-gray-400 mt-0.5">{hint}</p>}
        </div>
      </div>
    </div>
  );
}

/* ============================== upgrade gate ============================== */

function UpgradeGate({ onUpgrade }) {
  const { t } = useTranslation();
  return (
    <div className="bg-gradient-to-br from-primary-600 via-purple-600 to-pink-600 rounded-2xl p-8 text-white text-center shadow-xl">
      <Lock className="w-10 h-10 mx-auto mb-3" />
      <h2 className="text-2xl font-bold mb-2">{t('recruiter.analytics.proFeature')}</h2>
      <p className="text-white/85 max-w-md mx-auto text-sm mb-5">
        {t('recruiter.analytics.proDesc')}
      </p>
      <button
        onClick={onUpgrade}
        className="inline-flex items-center gap-2 bg-white text-primary-700 font-semibold rounded-full px-5 py-2.5 hover:scale-[1.02] transition-transform"
      >
        <Sparkles className="w-4 h-4" />
        {t('recruiter.analytics.upgradeToPro')}
      </button>
    </div>
  );
}

/* ============================== page ============================== */

export default function RecruiterAnalyticsPage() {
  const { t } = useTranslation();
  const { user, fetchUser } = useRecruiterGate();
  const effectiveUser = useAuthStore((s) => s.user) || user;

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [locked, setLocked] = useState(false);

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
        const res = await api.get('/recruiters/analytics/');
        setData(res.data);
      } catch (e) {
        if (e.response?.status === 401) {
          window.location.href = '/login?redirect=/recruiter/analytics';
          return;
        }
        if (e.response?.status === 403) {
          setLocked(true);
        } else {
          setError(t('recruiter.analytics.loadError'));
        }
      } finally {
        setLoading(false);
      }
    };
    run();
  }, [fetchUser]);

  if (loading) {
    return (
      <RecruiterLayout user={effectiveUser}>
        <div className="flex items-center justify-center min-h-[60vh]">
          <Loader2 className="w-10 h-10 text-primary-600 animate-spin" />
        </div>
      </RecruiterLayout>
    );
  }

  if (locked) {
    return (
      <RecruiterLayout user={effectiveUser}>
        <UpgradeGate onUpgrade={() => (window.location.href = '/recruiter/dashboard')} />
      </RecruiterLayout>
    );
  }

  if (error || !data) {
    return (
      <RecruiterLayout user={effectiveUser}>
        <div className="rounded-xl border border-red-200 dark:border-red-900/50 bg-red-50 dark:bg-red-950/30 px-4 py-3 text-sm text-red-700 dark:text-red-300">
          {error || t('recruiter.analytics.noDataAvailable')}
        </div>
      </RecruiterLayout>
    );
  }

  const pool = data.candidate_pool || {};
  const market = data.market_intelligence || {};
  const perf = data.my_jobs_performance || {};
  const pred = data.predictions || {};
  const ai = data.ai_matching || {};

  return (
    <RecruiterLayout user={effectiveUser}>
      {/* Header */}
      <div className="bg-gradient-to-r from-primary-600 via-purple-600 to-pink-600 rounded-2xl p-6 sm:p-8 text-white mb-6 shadow-lg">
        <div className="flex items-center gap-2 text-primary-100 text-xs font-medium uppercase tracking-wide mb-2">
          <Sparkles className="w-3.5 h-3.5" />
          {t('recruiter.analytics.headerBadge')}
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">{t('recruiter.analytics.headerTitle')}</h1>
        <p className="text-white/85 text-sm mt-2 max-w-2xl">
          {t('recruiter.analytics.headerSubtitle')}
        </p>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
        <KpiCard icon={Users} label={t('recruiter.analytics.openCandidates')} value={fmt(pool.total_open || 0)} accent="primary" />
        <KpiCard icon={Briefcase} label={t('recruiter.analytics.activeJobPosts')} value={fmt(perf.active_count || 0)} accent="green" />
        <KpiCard icon={Eye} label={t('recruiter.analytics.totalViews')} value={fmt(perf.total_views || 0)} accent="amber" />
        <KpiCard
          icon={Send}
          label={t('recruiter.analytics.applications')}
          value={fmt(perf.total_applications || 0)}
          hint={t('recruiter.analytics.rateLabel', { rate: fmtRate(perf.application_rate) })}
          accent="pink"
        />
      </div>

      {/* ===================== CANDIDATE POOL ===================== */}
      <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mt-2 mb-3 flex items-center gap-2">
        <Users className="w-4.5 h-4.5 text-primary-600" />
        {t('recruiter.analytics.candidatePoolTitle')}
      </h2>
      <div className="grid lg:grid-cols-2 gap-5 mb-8">
        <ChartCard icon={Briefcase} title={t('recruiter.analytics.candidatesByRole')} subtitle={t('recruiter.analytics.candidatesByRoleSub')}>
          <HBars
            data={(pool.by_role || []).map((r) => ({ ...r, label: r.role }))}
            valueKey="count"
            renderTooltip={(it) => `${it.role}: ${fmt(it.count)} candidates`}
          />
        </ChartCard>
        <ChartCard icon={Layers} title={t('recruiter.analytics.topSkills')} subtitle={t('recruiter.analytics.topSkillsSub')}>
          <HBars
            data={(pool.top_skills || []).map((r) => ({ ...r, label: r.skill }))}
            valueKey="count"
            renderTooltip={(it) => `${it.skill} (${it.category}): ${fmt(it.count)} candidates`}
          />
        </ChartCard>
        <ChartCard icon={TrendingUp} title={t('recruiter.analytics.experienceBreakdown')} subtitle={t('recruiter.analytics.experienceBreakdownSub')}>
          <Donut
            data={(pool.experience || []).map((r) => ({ ...r, label: r.label }))}
            valueKey="count"
          />
        </ChartCard>
        <ChartCard icon={MapPin} title={t('recruiter.analytics.locationHeatmap')} subtitle={t('recruiter.analytics.locationHeatmapSub')}>
          <HeatmapBlocks items={pool.locations || []} />
        </ChartCard>
      </div>

      {/* ===================== MARKET INTELLIGENCE ===================== */}
      <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mt-2 mb-3 flex items-center gap-2">
        <TrendingUp className="w-4.5 h-4.5 text-primary-600" />
        {t('recruiter.analytics.marketIntelligence')}
      </h2>
      <div className="grid lg:grid-cols-2 gap-5 mb-8">
        <ChartCard
          icon={Target}
          title={t('recruiter.analytics.inDemandSkills')}
          subtitle={t('recruiter.analytics.inDemandSkillsSub')}
        >
          <HBars
            data={(market.in_demand_skills || []).map((s) => ({ ...s, label: s.skill }))}
            valueKey="job_count"
            renderTooltip={(it) =>
              `${it.skill} — ${fmt(it.job_count)} jobs · ${fmt(it.candidate_count)} candidates have it`
            }
          />
        </ChartCard>
        <ChartCard
          icon={Briefcase}
          title={t('recruiter.analytics.avgSalaryByRole')}
          subtitle={t('recruiter.analytics.avgSalaryByRoleSub')}
        >
          <GroupedBars rows={market.salary_by_role || []} />
        </ChartCard>
        <ChartCard
          icon={AlertTriangle}
          title={t('recruiter.analytics.skillsGap')}
          subtitle={t('recruiter.analytics.skillsGapSub')}
        >
          <HBars
            data={(market.skills_gap || []).map((s) => ({ ...s, label: s.skill }))}
            valueKey="gap_score"
            formatValue={(v) => `${v}`}
            renderTooltip={(it) =>
              `${it.skill}: ${fmt(it.demand)} jobs · only ${fmt(it.supply)} candidates · gap ${it.gap_score}`
            }
          />
        </ChartCard>
        <ChartCard icon={Layers} title={t('recruiter.analytics.competitorPostings')} subtitle={t('recruiter.analytics.competitorPostingsSub')}>
          <HBars
            data={(market.competitor_postings || []).map((c) => ({ ...c, label: c.role }))}
            valueKey="count"
            renderTooltip={(it) => `${it.role}: ${fmt(it.count)} active competitor posts`}
          />
        </ChartCard>
      </div>

      {/* ===================== JOB PERFORMANCE ===================== */}
      <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mt-2 mb-3 flex items-center gap-2">
        <Briefcase className="w-4.5 h-4.5 text-primary-600" />
        {t('recruiter.analytics.yourJobPerformance')}
      </h2>
      <div className="grid lg:grid-cols-3 gap-5 mb-8">
        <div className="lg:col-span-2">
          <ChartCard icon={Eye} title={t('recruiter.analytics.perJobPerformance')} subtitle={t('recruiter.analytics.perJobPerformanceSub')}>
            {perf.jobs && perf.jobs.length > 0 ? (
              <div className="overflow-x-auto -mx-2">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-xs uppercase text-gray-500 dark:text-gray-400">
                      <th className="text-left font-medium px-2 py-2">{t('recruiter.analytics.job')}</th>
                      <th className="text-right font-medium px-2 py-2">{t('recruiter.analytics.views')}</th>
                      <th className="text-right font-medium px-2 py-2">{t('recruiter.analytics.apps')}</th>
                      <th className="text-right font-medium px-2 py-2">{t('recruiter.analytics.rate')}</th>
                      <th className="text-right font-medium px-2 py-2">{t('recruiter.analytics.days')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {perf.jobs.map((j) => (
                      <tr
                        key={j.job_id}
                        className="border-t border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50"
                      >
                        <td className="px-2 py-2">
                          <div className="font-medium text-gray-900 dark:text-gray-100 truncate max-w-[260px]">
                            {j.title}
                          </div>
                          <div className="text-[11px] text-gray-500">
                            {j.category} ·{' '}
                            <span
                              className={
                                j.status === 'active'
                                  ? 'text-emerald-600'
                                  : j.status === 'draft'
                                  ? 'text-amber-600'
                                  : 'text-gray-500'
                              }
                            >
                              {j.status}
                            </span>
                          </div>
                        </td>
                        <td className="text-right tabular-nums px-2 py-2">{fmt(j.views)}</td>
                        <td className="text-right tabular-nums px-2 py-2">{fmt(j.applications)}</td>
                        <td className="text-right tabular-nums px-2 py-2">{fmtRate(j.application_rate)}</td>
                        <td className="text-right tabular-nums px-2 py-2 text-gray-500">
                          {j.days_since_posted ?? '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-sm text-gray-500 py-6 text-center">
                {t('recruiter.analytics.noJobsPosted')}{' '}
                <Link to="/recruiter/jobs/new" className="text-primary-600 font-medium no-underline">
                  {t('recruiter.analytics.postRole')}
                </Link>
              </p>
            )}
          </ChartCard>
        </div>
        <ChartCard icon={Trophy} title={t('recruiter.analytics.bestPerformingJob')} subtitle={t('recruiter.analytics.bestPerformingJobSub')}>
          {perf.best_job ? (
            <div className="space-y-3">
              <div className="rounded-lg bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-950/40 dark:to-orange-950/40 border border-amber-200 dark:border-amber-900/40 p-4">
                <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">{perf.best_job.title}</p>
                <p className="text-xs text-gray-500 mt-0.5">{perf.best_job.category}</p>
              </div>
              <div className="grid grid-cols-3 gap-2 text-center">
                <div>
                  <p className="text-lg font-bold tabular-nums">{fmt(perf.best_job.applications)}</p>
                  <p className="text-[11px] text-gray-500">{t('recruiter.analytics.apps')}</p>
                </div>
                <div>
                  <p className="text-lg font-bold tabular-nums">{fmt(perf.best_job.views)}</p>
                  <p className="text-[11px] text-gray-500">{t('recruiter.analytics.views')}</p>
                </div>
                <div>
                  <p className="text-lg font-bold tabular-nums">{fmtRate(perf.best_job.application_rate)}</p>
                  <p className="text-[11px] text-gray-500">{t('recruiter.analytics.rate')}</p>
                </div>
              </div>
              <div className="flex items-center gap-1.5 text-xs text-gray-500">
                <Calendar className="w-3.5 h-3.5" />
                {t('recruiter.analytics.postedDaysAgo', { count: perf.best_job.days_since_posted })}
              </div>
            </div>
          ) : (
            <p className="text-sm text-gray-500 py-6 text-center">{t('recruiter.analytics.noJobActivity')}</p>
          )}
        </ChartCard>
      </div>

      {/* ===================== PREDICTIONS ===================== */}
      <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mt-2 mb-3 flex items-center gap-2">
        <TrendingUp className="w-4.5 h-4.5 text-primary-600" />
        {t('recruiter.analytics.predictionsTitle')}
      </h2>
      <div className="grid lg:grid-cols-2 gap-5 mb-8">
        <ChartCard
          icon={ArrowUpRight}
          title={t('recruiter.analytics.hotSkillsNextQuarter')}
          subtitle={t('recruiter.analytics.hotSkillsNextQuarterSub')}
        >
          <HBars
            data={(pred.next_quarter_hot_skills || []).map((s) => ({ ...s, label: s.skill }))}
            valueKey="demand_change_30d"
            formatValue={(v) => `${v > 0 ? '+' : ''}${v}%`}
            renderTooltip={(it) =>
              `${it.skill}: ${it.demand_change_30d > 0 ? '+' : ''}${it.demand_change_30d}% in 30d · ${fmt(it.job_count)} jobs`
            }
          />
        </ChartCard>
        <ChartCard
          icon={Target}
          title={t('recruiter.analytics.competitorAnalysis')}
          subtitle={t('recruiter.analytics.competitorAnalysisSub')}
        >
          <HBars
            data={(pred.competitor_skills || []).map((s) => ({ ...s, label: s.skill }))}
            valueKey="count"
            renderTooltip={(it) => `${it.skill}: ${fmt(it.count)} competitor postings`}
          />
        </ChartCard>
      </div>

      {/* ===================== AI MATCHING ===================== */}
      <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mt-2 mb-3 flex items-center gap-2">
        <Brain className="w-4.5 h-4.5 text-primary-600" />
        {t('recruiter.analytics.aiMatchingTitle')}
      </h2>
      <div className="grid lg:grid-cols-3 gap-5 mb-8">
        <div className="lg:col-span-2 space-y-5">
          <ChartCard icon={Users} title={t('recruiter.analytics.topMatchedCandidates')} subtitle={t('recruiter.analytics.topMatchedCandidatesSub')}>
            {(ai.top_candidates_per_job || []).length === 0 ? (
              <p className="text-sm text-gray-500 py-6 text-center">
                {t('recruiter.analytics.postJobToSeeMatches')}
              </p>
            ) : (
              <div className="space-y-4">
                {ai.top_candidates_per_job.map((j) => (
                  <div key={j.job_id} className="rounded-lg border border-gray-100 dark:border-gray-800 p-3">
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <p className="text-sm font-semibold text-gray-900 dark:text-gray-100 truncate">{j.title}</p>
                      <span className="text-[11px] text-gray-500 whitespace-nowrap">
                        {t('recruiter.analytics.reqSkills', { count: j.required_skill_count })}
                      </span>
                    </div>
                    {j.candidates && j.candidates.length > 0 ? (
                      <ul className="space-y-1.5">
                        {j.candidates.map((c) => (
                          <li
                            key={c.user_id}
                            className="flex items-center justify-between gap-2 text-xs"
                          >
                            <Link
                              to={`/recruiter/candidates/${c.user_id}`}
                              className="flex items-center gap-2 min-w-0 no-underline text-gray-700 dark:text-gray-200 hover:text-primary-600"
                            >
                              <div className="w-7 h-7 rounded-full bg-primary-100 dark:bg-primary-900/40 text-primary-700 flex items-center justify-center text-[11px] font-semibold flex-shrink-0">
                                {(c.name || c.email || '?').charAt(0).toUpperCase()}
                              </div>
                              <div className="min-w-0">
                                <p className="font-medium truncate">{c.name || c.email}</p>
                                <p className="text-[10px] text-gray-500 truncate">
                                  {c.desired_role || '—'}
                                  {c.experience_level ? ` · ${c.experience_level}` : ''}
                                </p>
                              </div>
                            </Link>
                            <div className="flex items-center gap-2 flex-shrink-0">
                              <div className="w-20 h-1.5 rounded-full bg-gray-100 dark:bg-gray-800 overflow-hidden">
                                <div
                                  className="h-full bg-gradient-to-r from-primary-500 to-purple-500"
                                  style={{ width: `${Math.min(c.match_pct, 100)}%` }}
                                />
                              </div>
                              <span className="font-semibold tabular-nums w-10 text-right">
                                {c.match_pct}%
                              </span>
                            </div>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-xs text-gray-500">{j.note || t('recruiter.analytics.noCandidatesMatch')}</p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </ChartCard>
        </div>
        <div className="space-y-5">
          <ChartCard icon={AlertTriangle} title={t('recruiter.analytics.hardestToFill')} subtitle={t('recruiter.analytics.hardestToFillSub')}>
            {(ai.hardest_to_fill || []).length === 0 ? (
              <p className="text-sm text-gray-500 py-6 text-center">{t('recruiter.analytics.noData')}</p>
            ) : (
              <ul className="space-y-3">
                {ai.hardest_to_fill.map((j) => (
                  <li key={j.job_id} className="text-xs">
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <span className="font-medium text-gray-800 dark:text-gray-200 truncate">{j.title}</span>
                      <span className="font-semibold tabular-nums">{j.avg_top_match}%</span>
                    </div>
                    <div className="h-1.5 rounded-full bg-gray-100 dark:bg-gray-800 overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-rose-500 to-amber-500"
                        style={{ width: `${Math.min(j.avg_top_match, 100)}%` }}
                      />
                    </div>
                    <p className="text-[10px] text-gray-500 mt-0.5">
                      {fmt(j.matched_candidates)} candidates partially match
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </ChartCard>

          <ChartCard icon={Sparkles} title={t('recruiter.analytics.suggestedSkills')} subtitle={t('recruiter.analytics.suggestedSkillsSub')}>
            {(ai.suggested_skills_per_job || []).length === 0 ? (
              <p className="text-sm text-gray-500 py-6 text-center">{t('recruiter.analytics.noSuggestions')}</p>
            ) : (
              <ul className="space-y-3">
                {ai.suggested_skills_per_job.map((j) => (
                  <li key={j.job_id} className="text-xs">
                    <p className="font-medium text-gray-800 dark:text-gray-200 truncate mb-1.5">{j.title}</p>
                    {j.missing_skills && j.missing_skills.length > 0 ? (
                      <div className="flex flex-wrap gap-1.5">
                        {j.missing_skills.map((s) => (
                          <span
                            key={s.skill_id}
                            className="px-2 py-0.5 rounded-full bg-primary-50 dark:bg-primary-950/40 text-primary-700 dark:text-primary-300 text-[11px] font-medium"
                            title={`${s.demand} peer postings require this`}
                          >
                            {s.skill}
                            <span className="ml-1 text-primary-400">+{s.demand}</span>
                          </span>
                        ))}
                      </div>
                    ) : (
                      <p className="text-[11px] text-gray-500">{j.note || t('recruiter.analytics.alreadyCovered')}</p>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </ChartCard>
        </div>
      </div>

      <p className="text-[11px] text-gray-400 text-center mt-2">
        {t('recruiter.analytics.generatedAt')} {data.generated_at ? new Date(data.generated_at).toLocaleString() : '—'}
      </p>
    </RecruiterLayout>
  );
}
