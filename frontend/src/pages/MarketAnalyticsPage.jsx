import { useState, useEffect, useMemo } from 'react';
import {
  TrendingUp, TrendingDown, Briefcase, BarChart3, Code2,
  Clock, Building2, Wifi, DollarSign, Loader2, AlertCircle,
  ChevronDown, ArrowUpRight, ArrowDownRight, Minus, Users,
  Zap, Globe,
} from 'lucide-react';
import api from '../services/api';
import useAuthStore from '../store/authStore';
import DashboardLayout from '../components/layout/DashboardLayout';

/* ── Helpers ────────────────────────────────────────────────────── */

function formatSalary(value) {
  if (!value) return '—';
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(0)}K`;
  return value.toString();
}

function formatHoursAgo(hours) {
  if (hours === null || hours === undefined) return 'Unknown';
  if (hours < 1) return 'Less than 1 hour ago';
  if (hours < 24) return `${Math.round(hours)} hour${Math.round(hours) !== 1 ? 's' : ''} ago`;
  const days = Math.round(hours / 24);
  return `${days} day${days !== 1 ? 's' : ''} ago`;
}

function TrendBadge({ value }) {
  if (value === null || value === undefined) return <span className="text-xs text-gray-400">—</span>;
  const isUp = value > 0;
  const isDown = value < 0;
  return (
    <span className={`inline-flex items-center gap-0.5 text-xs font-medium ${isUp ? 'text-emerald-600' : isDown ? 'text-red-500' : 'text-gray-400'}`}>
      {isUp ? <ArrowUpRight className="w-3 h-3" /> : isDown ? <ArrowDownRight className="w-3 h-3" /> : <Minus className="w-3 h-3" />}
      {Math.abs(value).toFixed(1)}%
    </span>
  );
}

/* ── Mini bar chart (pure CSS) ──────────────────────────────────── */

function MiniBar({ value, max, color = 'bg-primary-500' }) {
  const pct = max > 0 ? (value / max) * 100 : 0;
  return (
    <div className="w-full h-2 bg-gray-100 rounded-full">
      <div className={`h-2 rounded-full ${color}`} style={{ width: `${Math.min(pct, 100)}%` }} />
    </div>
  );
}

/* ── Header Section ─────────────────────────────────────────────── */

function PageHeader({ overview }) {
  const totalJobs = overview?.total_active_jobs ?? 0;
  const hoursAgo = overview?.last_updated_hours_ago;

  return (
    <div className="mb-8">
      <div className="flex items-center gap-3 mb-2">
        <div className="w-10 h-10 bg-gradient-to-br from-primary-600 to-purple-500 rounded-xl flex items-center justify-center">
          <BarChart3 className="w-5 h-5 text-white" />
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
          Market Analytics Dashboard
        </h1>
      </div>
      <p className="text-gray-500 text-sm sm:text-base">
        Real-time insights from <span className="font-semibold text-gray-700">{totalJobs.toLocaleString()}</span> active job postings across Uzbekistan IT market
      </p>
      <p className="text-xs text-gray-400 mt-1 flex items-center gap-1">
        <Clock className="w-3 h-3" />
        Last updated: {formatHoursAgo(hoursAgo)}
      </p>
    </div>
  );
}

/* ── Overview Stats Cards ───────────────────────────────────────── */

function OverviewStats({ overview }) {
  const cards = [
    {
      label: 'Active Jobs',
      value: overview?.total_active_jobs?.toLocaleString() ?? '—',
      sub: `${overview?.jobs_posted_last_7d ?? 0} new this week`,
      icon: <Briefcase className="w-5 h-5 text-primary-600" />,
      iconBg: 'bg-primary-100',
    },
    {
      label: 'Companies Hiring',
      value: overview?.total_companies?.toLocaleString() ?? '—',
      sub: 'Unique employers',
      icon: <Building2 className="w-5 h-5 text-emerald-600" />,
      iconBg: 'bg-emerald-100',
    },
    {
      label: 'Skills in Demand',
      value: overview?.skills_in_demand?.toLocaleString() ?? '—',
      sub: `${overview?.total_skills_tracked ?? 0} total tracked`,
      icon: <Code2 className="w-5 h-5 text-purple-600" />,
      iconBg: 'bg-purple-100',
    },
    {
      label: 'Avg Salary Range',
      value: overview?.salary_overview?.avg_min
        ? `${formatSalary(overview.salary_overview.avg_min)} – ${formatSalary(overview.salary_overview.avg_max)}`
        : '—',
      sub: overview?.salary_overview?.median ? `Median: ${formatSalary(overview.salary_overview.median)}` : 'UZS',
      icon: <DollarSign className="w-5 h-5 text-amber-600" />,
      iconBg: 'bg-amber-100',
    },
    {
      label: 'Remote Jobs',
      value: overview?.remote_jobs_percentage != null ? `${overview.remote_jobs_percentage}%` : '—',
      sub: 'Remote-friendly positions',
      icon: <Wifi className="w-5 h-5 text-blue-600" />,
      iconBg: 'bg-blue-100',
    },
    {
      label: 'Jobs (30 days)',
      value: overview?.jobs_posted_last_30d?.toLocaleString() ?? '—',
      sub: 'Posted in last month',
      icon: <Globe className="w-5 h-5 text-orange-600" />,
      iconBg: 'bg-orange-100',
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
      {cards.map((c, i) => (
        <div key={i} className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow">
          <div className={`w-10 h-10 ${c.iconBg} rounded-lg flex items-center justify-center mb-3`}>
            {c.icon}
          </div>
          <p className="text-2xl font-bold text-gray-900">{c.value}</p>
          <p className="text-sm font-medium text-gray-600 mt-0.5">{c.label}</p>
          <p className="text-xs text-gray-400 mt-1">{c.sub}</p>
        </div>
      ))}
    </div>
  );
}

/* ── Trending Skills Table ──────────────────────────────────────── */

function TrendingSkills({ skills, period, onPeriodChange }) {
  const maxJobCount = useMemo(() => {
    if (!skills?.length) return 1;
    return Math.max(...skills.map((s) => s.job_count));
  }, [skills]);

  const CATEGORY_COLORS = {
    programming_language: 'bg-blue-100 text-blue-700',
    framework: 'bg-purple-100 text-purple-700',
    database: 'bg-emerald-100 text-emerald-700',
    devops: 'bg-orange-100 text-orange-700',
    cloud: 'bg-sky-100 text-sky-700',
    tool: 'bg-gray-100 text-gray-700',
    soft_skill: 'bg-pink-100 text-pink-700',
  };

  return (
    <Section title="Trending Skills" subtitle="Most in-demand skills by job postings">
      {/* Period filter */}
      <div className="flex gap-2 mb-5">
        {['7d', '30d', '90d', 'all'].map((p) => (
          <button
            key={p}
            onClick={() => onPeriodChange(p)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium border-none cursor-pointer transition-colors ${
              period === p
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {p === '7d' ? '7 Days' : p === '30d' ? '30 Days' : p === '90d' ? '90 Days' : 'All Time'}
          </button>
        ))}
      </div>

      {!skills?.length ? (
        <p className="text-sm text-gray-400 text-center py-8">No trend data available yet.</p>
      ) : (
        <div className="space-y-3">
          {/* Header */}
          <div className="grid grid-cols-12 gap-2 text-xs font-medium text-gray-400 px-2">
            <div className="col-span-1">#</div>
            <div className="col-span-4">Skill</div>
            <div className="col-span-3">Jobs</div>
            <div className="col-span-2 text-right">Salary</div>
            <div className="col-span-2 text-right">Trend</div>
          </div>

          {skills.map((s, i) => (
            <div key={s.skill_id} className="grid grid-cols-12 gap-2 items-center bg-gray-50 rounded-lg px-3 py-2.5 hover:bg-gray-100 transition-colors">
              <div className="col-span-1">
                <span className={`text-xs font-bold ${i < 3 ? 'text-primary-600' : 'text-gray-400'}`}>
                  {s.rank}
                </span>
              </div>
              <div className="col-span-4">
                <p className="text-sm font-semibold text-gray-900 truncate">{s.skill_name}</p>
                <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${CATEGORY_COLORS[s.category] || 'bg-gray-100 text-gray-600'}`}>
                  {(s.category || 'other').replace(/_/g, ' ')}
                </span>
              </div>
              <div className="col-span-3">
                <p className="text-sm font-medium text-gray-700 mb-1">{s.job_count}</p>
                <MiniBar value={s.job_count} max={maxJobCount} />
              </div>
              <div className="col-span-2 text-right">
                <p className="text-sm font-medium text-gray-700">
                  {s.avg_salary ? `${formatSalary(s.avg_salary)}` : '—'}
                </p>
                {s.avg_salary && <p className="text-[10px] text-gray-400">UZS</p>}
              </div>
              <div className="col-span-2 text-right">
                <TrendBadge value={s.demand_change_30d ?? s.demand_change_7d} />
              </div>
            </div>
          ))}
        </div>
      )}
    </Section>
  );
}

/* ── Job Categories ─────────────────────────────────────────────── */

function JobCategories({ categories }) {
  const maxCount = useMemo(() => {
    if (!categories?.length) return 1;
    return Math.max(...categories.map((c) => c.job_count));
  }, [categories]);

  const COLORS = [
    'bg-primary-500', 'bg-emerald-500', 'bg-purple-500', 'bg-amber-500',
    'bg-blue-500', 'bg-orange-500', 'bg-pink-500', 'bg-teal-500',
  ];

  return (
    <Section title="Jobs by Category" subtitle="Open positions by specialization">
      {!categories?.length ? (
        <p className="text-sm text-gray-400 text-center py-8">No category data available yet.</p>
      ) : (
        <div className="space-y-4">
          {categories.map((cat, i) => (
            <div key={cat.category} className="flex items-center gap-3">
              <div className="w-28 sm:w-36 flex-shrink-0">
                <p className="text-sm font-medium text-gray-900 truncate">{cat.category}</p>
              </div>
              <div className="flex-1">
                <MiniBar value={cat.job_count} max={maxCount} color={COLORS[i % COLORS.length]} />
              </div>
              <div className="w-16 text-right flex-shrink-0">
                <span className="text-sm font-bold text-gray-700">{cat.job_count}</span>
              </div>
              <div className="w-24 text-right flex-shrink-0 hidden sm:block">
                {cat.avg_salary_min ? (
                  <span className="text-xs text-gray-500">
                    {formatSalary(cat.avg_salary_min)} – {formatSalary(cat.avg_salary_max)}
                  </span>
                ) : (
                  <span className="text-xs text-gray-400">—</span>
                )}
              </div>
              {cat.change_7d != null && (
                <div className="w-14 text-right flex-shrink-0 hidden sm:block">
                  <TrendBadge value={cat.change_7d} />
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </Section>
  );
}

/* ── Salary Insights ────────────────────────────────────────────── */

function SalaryInsights({ salaries, expFilter, onExpFilterChange }) {
  const data = salaries?.salaries || [];

  return (
    <Section title="Salary Insights by Role" subtitle="Average salary ranges across IT positions">
      {/* Experience filter */}
      <div className="flex flex-wrap gap-2 mb-5">
        {[
          { value: 'all', label: 'All Levels' },
          { value: 'no_experience', label: 'No Exp' },
          { value: 'junior', label: 'Junior' },
          { value: 'mid', label: 'Mid' },
          { value: 'senior', label: 'Senior' },
        ].map((opt) => (
          <button
            key={opt.value}
            onClick={() => onExpFilterChange(opt.value)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium border-none cursor-pointer transition-colors ${
              expFilter === opt.value
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {!data.length ? (
        <p className="text-sm text-gray-400 text-center py-8">No salary data available yet.</p>
      ) : (
        <div className="space-y-3">
          {data.map((s, i) => {
            const avgMin = s.salary_min || s.salary_avg;
            const avgMax = s.salary_max || s.salary_avg;
            const barMin = avgMin ? (avgMin / (data[0]?.salary_max || avgMax || 1)) * 100 : 0;
            const barMax = avgMax ? (avgMax / (data[0]?.salary_max || avgMax || 1)) * 100 : 0;

            return (
              <div key={i} className="bg-gray-50 rounded-lg px-4 py-3 hover:bg-gray-100 transition-colors">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-gray-900 truncate">{s.job_title}</p>
                    <p className="text-xs text-gray-400">{s.job_count} posting{s.job_count !== 1 ? 's' : ''}</p>
                  </div>
                  <div className="text-right flex-shrink-0 ml-3">
                    <p className="text-sm font-bold text-gray-900">
                      {formatSalary(avgMin)} – {formatSalary(avgMax)}
                    </p>
                    <p className="text-[10px] text-gray-400">{s.currency || 'UZS'}</p>
                  </div>
                </div>

                {/* Salary range bar */}
                <div className="relative w-full h-2 bg-gray-200 rounded-full">
                  <div
                    className="absolute h-2 bg-gradient-to-r from-primary-400 to-purple-500 rounded-full"
                    style={{
                      left: `${Math.min(barMin, 100)}%`,
                      width: `${Math.max(barMax - barMin, 5)}%`,
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </Section>
  );
}

/* ── Experience Distribution ────────────────────────────────────── */

function ExperienceDistribution({ distribution }) {
  if (!distribution || Object.keys(distribution).length === 0) return null;

  const LABELS = {
    no_experience: 'No Experience',
    junior: 'Junior (1-3y)',
    mid: 'Mid-Level (3-6y)',
    senior: 'Senior (6+y)',
    '': 'Not Specified',
    null: 'Not Specified',
  };

  const COLORS = {
    no_experience: 'bg-emerald-500',
    junior: 'bg-blue-500',
    mid: 'bg-purple-500',
    senior: 'bg-orange-500',
  };

  const total = Object.values(distribution).reduce((a, b) => a + b, 0);
  const entries = Object.entries(distribution)
    .map(([key, count]) => ({
      key,
      label: LABELS[key] || key || 'Other',
      count,
      pct: total > 0 ? (count / total) * 100 : 0,
      color: COLORS[key] || 'bg-gray-400',
    }))
    .sort((a, b) => b.count - a.count);

  return (
    <Section title="Experience Level Distribution" subtitle={`Based on ${total.toLocaleString()} job postings`}>
      {/* Stacked bar */}
      <div className="flex w-full h-8 rounded-lg overflow-hidden mb-4">
        {entries.map((e) => (
          <div
            key={e.key}
            className={`${e.color} relative group`}
            style={{ width: `${e.pct}%` }}
            title={`${e.label}: ${e.count} (${e.pct.toFixed(1)}%)`}
          />
        ))}
      </div>

      {/* Legend */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {entries.map((e) => (
          <div key={e.key} className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-sm ${e.color} flex-shrink-0`} />
            <div>
              <p className="text-xs font-medium text-gray-700">{e.label}</p>
              <p className="text-xs text-gray-400">{e.count.toLocaleString()} ({e.pct.toFixed(1)}%)</p>
            </div>
          </div>
        ))}
      </div>
    </Section>
  );
}

/* ── Top Skills per Category ────────────────────────────────────── */

function TopSkillsByCategory({ categories }) {
  const withSkills = (categories || []).filter((c) => c.top_skills?.length > 0).slice(0, 6);

  if (!withSkills.length) return null;

  return (
    <Section title="Top Skills by Category" subtitle="Most requested skills in each job category">
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {withSkills.map((cat) => (
          <div key={cat.category} className="bg-gray-50 rounded-xl p-4">
            <h4 className="text-sm font-bold text-gray-900 mb-3">{cat.category}</h4>
            <div className="space-y-2">
              {cat.top_skills.slice(0, 5).map((skill, i) => (
                <div key={skill.skill_id || i} className="flex items-center justify-between">
                  <span className="text-xs text-gray-700">{skill.name}</span>
                  <span className="text-xs font-medium text-primary-600">{skill.count} jobs</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </Section>
  );
}

/* ── Top Job Titles ────────────────────────────────────────────── */

function TopJobTitles({ titles, period, onPeriodChange }) {
  const maxCount = useMemo(() => {
    if (!titles?.length) return 1;
    return Math.max(...titles.map((t) => t.count));
  }, [titles]);

  const RANK_COLORS = [
    'bg-amber-400 text-white',   // gold
    'bg-gray-400 text-white',    // silver
    'bg-orange-600 text-white',  // bronze
  ];

  return (
    <Section title="Top Job Titles" subtitle="Most posted positions in the market">
      {/* Period filter */}
      <div className="flex gap-2 mb-5">
        {['7d', '30d', '90d', 'all'].map((p) => (
          <button
            key={p}
            onClick={() => onPeriodChange(p)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium border-none cursor-pointer transition-colors ${
              period === p
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {p === '7d' ? '7 Days' : p === '30d' ? '30 Days' : p === '90d' ? '90 Days' : 'All Time'}
          </button>
        ))}
      </div>

      {!titles?.length ? (
        <p className="text-sm text-gray-400 text-center py-8">No job title data available yet.</p>
      ) : (
        <div className="space-y-2.5">
          {titles.map((t, i) => (
            <div key={t.job_title} className="flex items-center gap-3 bg-gray-50 rounded-lg px-3 py-2.5 hover:bg-gray-100 transition-colors">
              <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 ${
                i < 3 ? RANK_COLORS[i] : 'bg-gray-200 text-gray-500'
              }`}>
                {i + 1}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">{t.job_title}</p>
                <div className="mt-1">
                  <MiniBar value={t.count} max={maxCount} color={i < 3 ? 'bg-primary-500' : 'bg-gray-400'} />
                </div>
              </div>
              <div className="flex-shrink-0 text-right">
                <span className="text-sm font-bold text-gray-700">{t.count}</span>
                <p className="text-[10px] text-gray-400">posts</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </Section>
  );
}

/* ── Section Wrapper ────────────────────────────────────────────── */

function Section({ title, subtitle, children }) {
  return (
    <section className="bg-white rounded-2xl border border-gray-200 p-6">
      <div className="mb-5">
        <h2 className="text-lg font-bold text-gray-900">{title}</h2>
        {subtitle && <p className="text-xs text-gray-400 mt-0.5">{subtitle}</p>}
      </div>
      {children}
    </section>
  );
}

/* ── Main Page ──────────────────────────────────────────────────── */

export default function MarketAnalyticsPage() {
  const { user, fetchUser } = useAuthStore();
  const [overview, setOverview] = useState(null);
  const [trendingSkills, setTrendingSkills] = useState([]);
  const [categories, setCategories] = useState([]);
  const [salaryData, setSalaryData] = useState(null);
  const [topTitles, setTopTitles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Filters
  const [skillPeriod, setSkillPeriod] = useState('30d');
  const [expFilter, setExpFilter] = useState('all');
  const [titlePeriod, setTitlePeriod] = useState('all');

  // Initial load
  useEffect(() => {
    const load = async () => {
      try {
        if (!user) await fetchUser();

        // Single dashboard endpoint gives us overview + trending + categories + salaries
        const { data } = await api.get('/analytics/dashboard/');

        setOverview(data.market_overview || {});
        setTrendingSkills(data.trending_skills || []);
        setCategories(data.job_categories || []);
        setSalaryData(data.top_salaries || { salaries: [] });
        setTopTitles(data.top_job_titles || []);
      } catch (err) {
        if (err.response?.status === 401) {
          window.location.href = '/login?redirect=/market-analytics';
          return;
        }
        setError('Failed to load analytics data.');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  // Reload trending skills when period changes
  useEffect(() => {
    if (loading) return;
    const fetchSkills = async () => {
      try {
        const { data } = await api.get('/analytics/market/skills/trending/', {
          params: { period: skillPeriod, limit: 20 },
        });
        setTrendingSkills(data.skills || []);
      } catch {
        // keep existing
      }
    };
    fetchSkills();
  }, [skillPeriod]);

  // Reload salaries when experience filter changes
  useEffect(() => {
    if (loading) return;
    const fetchSalaries = async () => {
      try {
        const { data } = await api.get('/analytics/market/salaries/', {
          params: { experience_level: expFilter, limit: 15 },
        });
        setSalaryData(data);
      } catch {
        // keep existing
      }
    };
    fetchSalaries();
  }, [expFilter]);

  // Reload top job titles when period changes
  useEffect(() => {
    if (loading) return;
    const fetchTitles = async () => {
      try {
        const { data } = await api.get('/analytics/market/top-titles/', {
          params: { period: titlePeriod, limit: 10 },
        });
        setTopTitles(data.titles || []);
      } catch {
        // keep existing
      }
    };
    fetchTitles();
  }, [titlePeriod]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-primary-600 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-10 h-10 text-red-400 mx-auto mb-3" />
          <p className="text-gray-600">{error}</p>
          <button onClick={() => window.location.reload()} className="mt-3 text-primary-600 text-sm font-medium underline bg-transparent border-none cursor-pointer">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <DashboardLayout user={user}>
      <div className="space-y-6">
        <PageHeader overview={overview} />
        <OverviewStats overview={overview} />

        <div className="grid lg:grid-cols-5 gap-6">
          {/* Left – wider */}
          <div className="lg:col-span-3 space-y-6">
            <TrendingSkills
              skills={trendingSkills}
              period={skillPeriod}
              onPeriodChange={setSkillPeriod}
            />
            <SalaryInsights
              salaries={salaryData}
              expFilter={expFilter}
              onExpFilterChange={setExpFilter}
            />
          </div>

          {/* Right */}
          <div className="lg:col-span-2 space-y-6">
            <TopJobTitles
              titles={topTitles}
              period={titlePeriod}
              onPeriodChange={setTitlePeriod}
            />
            <JobCategories categories={categories} />
            <ExperienceDistribution distribution={overview?.experience_distribution} />
            <TopSkillsByCategory categories={categories} />
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
