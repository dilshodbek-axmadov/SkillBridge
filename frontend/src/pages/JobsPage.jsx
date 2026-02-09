import { useState, useEffect, useMemo } from 'react';
import {
  Briefcase, Search, MapPin, Clock, ExternalLink, Filter,
  ChevronDown, Wifi, DollarSign, Star, X, Loader2,
} from 'lucide-react';
import DashboardLayout from '../components/layout/DashboardLayout';
import useAuthStore from '../store/authStore';
import api from '../services/api';

/* ── Helpers ───────────────────────────────────────────────────── */

function timeAgo(dateStr) {
  if (!dateStr) return '';
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 30) return `${days}d ago`;
  return `${Math.floor(days / 30)}mo ago`;
}

function formatSalary(min, max, currency) {
  const fmt = (n) => {
    if (!n) return null;
    if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
    if (n >= 1_000) return `${Math.round(n / 1_000)}K`;
    return n.toString();
  };
  const a = fmt(min);
  const b = fmt(max);
  if (a && b) return `${a} – ${b} ${currency || 'UZS'}`;
  if (a) return `from ${a} ${currency || 'UZS'}`;
  if (b) return `up to ${b} ${currency || 'UZS'}`;
  return null;
}

/* ── Match Ring ────────────────────────────────────────────────── */

function MatchRing({ pct, size = 44 }) {
  const r = (size - 6) / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ - (pct / 100) * circ;
  const color = pct >= 70 ? '#10b981' : pct >= 40 ? '#f59e0b' : '#ef4444';

  return (
    <div className="relative flex-shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#f3f4f6" strokeWidth={3} />
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={color} strokeWidth={3}
          strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round"
          className="transition-all duration-500" />
      </svg>
      <span className="absolute inset-0 flex items-center justify-center text-[11px] font-bold" style={{ color }}>
        {pct}%
      </span>
    </div>
  );
}

/* ── Job Card ──────────────────────────────────────────────────── */

function JobCard({ job, showMatch }) {
  const salary = formatSalary(job.salary_min, job.salary_max, job.salary_currency);
  const skills = job.skills || [];
  const matched = job.matched_skills || [];
  const missing = job.missing_skills || [];

  return (
    <div className="bg-white rounded-2xl border border-gray-100 p-5 hover:shadow-md hover:border-gray-200 transition-all group">
      <div className="flex gap-4">
        {/* Match ring */}
        {showMatch && job.match_percentage != null && (
          <MatchRing pct={job.match_percentage} />
        )}

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <h3 className="text-base font-bold text-gray-900 truncate">{job.job_title}</h3>
              <p className="text-sm text-gray-500 mt-0.5">{job.company_name || 'Company'}</p>
            </div>
            <a
              href={job.job_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-shrink-0 flex items-center gap-1.5 px-3 py-1.5 bg-primary-600 text-white text-xs font-semibold rounded-lg
                hover:bg-primary-700 transition-colors no-underline opacity-80 group-hover:opacity-100"
            >
              <span className="hidden sm:inline">View on hh.uz</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>

          {/* Meta badges */}
          <div className="flex flex-wrap items-center gap-2 mt-3">
            {job.location && (
              <span className="flex items-center gap-1 text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-lg">
                <MapPin className="w-3 h-3" />{job.location}
              </span>
            )}
            {job.is_remote && (
              <span className="flex items-center gap-1 text-xs text-emerald-700 bg-emerald-50 px-2 py-1 rounded-lg">
                <Wifi className="w-3 h-3" />Remote
              </span>
            )}
            {job.experience_required && (
              <span className="flex items-center gap-1 text-xs text-purple-700 bg-purple-50 px-2 py-1 rounded-lg">
                <Star className="w-3 h-3" />{job.experience_required.replace('_', ' ')}
              </span>
            )}
            {salary && (
              <span className="flex items-center gap-1 text-xs text-amber-700 bg-amber-50 px-2 py-1 rounded-lg font-medium">
                <DollarSign className="w-3 h-3" />{salary}
              </span>
            )}
            {job.posted_date && (
              <span className="flex items-center gap-1 text-xs text-gray-400">
                <Clock className="w-3 h-3" />{timeAgo(job.posted_date)}
              </span>
            )}
          </div>

          {/* Skills */}
          {showMatch && (matched.length > 0 || missing.length > 0) ? (
            <div className="flex flex-wrap gap-1.5 mt-3">
              {matched.map((s) => (
                <span key={s} className="text-[11px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-medium">{s}</span>
              ))}
              {missing.slice(0, 3).map((s) => (
                <span key={s} className="text-[11px] px-2 py-0.5 rounded-full bg-red-50 text-red-500 font-medium">{s}</span>
              ))}
              {missing.length > 3 && (
                <span className="text-[11px] px-2 py-0.5 rounded-full bg-gray-100 text-gray-400">+{missing.length - 3} more</span>
              )}
            </div>
          ) : skills.length > 0 ? (
            <div className="flex flex-wrap gap-1.5 mt-3">
              {skills.slice(0, 6).map((s) => (
                <span key={s.skill_id} className={`text-[11px] px-2 py-0.5 rounded-full font-medium ${
                  s.importance === 'core' ? 'bg-primary-50 text-primary-700' : 'bg-gray-100 text-gray-500'
                }`}>{s.name}</span>
              ))}
              {skills.length > 6 && (
                <span className="text-[11px] px-2 py-0.5 rounded-full bg-gray-100 text-gray-400">+{skills.length - 6}</span>
              )}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

/* ── Filters Panel ─────────────────────────────────────────────── */

function FiltersPanel({ filters, filterOptions, onChange, onClear }) {
  const hasFilters = filters.q || filters.category || filters.experience || filters.location || filters.is_remote;

  return (
    <div className="bg-white rounded-2xl border border-gray-100 p-5 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-gray-800 flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-400" /> Filters
        </h3>
        {hasFilters && (
          <button onClick={onClear} className="text-xs text-primary-600 hover:text-primary-700 bg-transparent border-none cursor-pointer font-medium">
            Clear all
          </button>
        )}
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          value={filters.q}
          onChange={(e) => onChange('q', e.target.value)}
          placeholder="Search jobs..."
          className="w-full h-10 pl-9 pr-3 rounded-xl border border-gray-200 text-sm text-gray-900 outline-none
            focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 transition-all"
        />
      </div>

      {/* Category */}
      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1.5">Category</label>
        <select
          value={filters.category}
          onChange={(e) => onChange('category', e.target.value)}
          className="w-full h-10 px-3 rounded-xl border border-gray-200 text-sm text-gray-900 bg-white outline-none
            focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
        >
          <option value="">All categories</option>
          {(filterOptions.categories || []).map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </div>

      {/* Experience */}
      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1.5">Experience</label>
        <select
          value={filters.experience}
          onChange={(e) => onChange('experience', e.target.value)}
          className="w-full h-10 px-3 rounded-xl border border-gray-200 text-sm text-gray-900 bg-white outline-none
            focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
        >
          <option value="">All levels</option>
          {(filterOptions.experience_levels || []).map((l) => (
            <option key={l.value} value={l.value}>{l.label}</option>
          ))}
        </select>
      </div>

      {/* Location */}
      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1.5">Location</label>
        <select
          value={filters.location}
          onChange={(e) => onChange('location', e.target.value)}
          className="w-full h-10 px-3 rounded-xl border border-gray-200 text-sm text-gray-900 bg-white outline-none
            focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
        >
          <option value="">All locations</option>
          {(filterOptions.locations || []).map((l) => (
            <option key={l} value={l}>{l}</option>
          ))}
        </select>
      </div>

      {/* Remote */}
      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-700">Remote only</span>
        <button
          type="button"
          onClick={() => onChange('is_remote', filters.is_remote ? '' : 'true')}
          className={`relative w-10 h-5.5 rounded-full transition-colors border-none cursor-pointer ${
            filters.is_remote ? 'bg-primary-600' : 'bg-gray-300'
          }`}
          style={{ width: 40, height: 22 }}
        >
          <span className={`absolute top-0.5 left-0.5 w-[18px] h-[18px] bg-white rounded-full shadow-sm transition-transform ${
            filters.is_remote ? 'translate-x-[18px]' : 'translate-x-0'
          }`} />
        </button>
      </div>

      {/* Sort */}
      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1.5">Sort by</label>
        <select
          value={filters.sort}
          onChange={(e) => onChange('sort', e.target.value)}
          className="w-full h-10 px-3 rounded-xl border border-gray-200 text-sm text-gray-900 bg-white outline-none
            focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
        >
          <option value="posted_date">Most recent</option>
          <option value="salary_max">Highest salary</option>
        </select>
      </div>
    </div>
  );
}

/* ── Main Jobs Page ────────────────────────────────────────────── */

export default function JobsPage() {
  const { user, fetchUser } = useAuthStore();
  const [tab, setTab] = useState('recommended'); // recommended | all
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);

  // Recommended
  const [recommended, setRecommended] = useState([]);
  const [recTotal, setRecTotal] = useState(0);

  // All jobs
  const [allJobs, setAllJobs] = useState([]);
  const [allTotal, setAllTotal] = useState(0);
  const [offset, setOffset] = useState(0);

  // Filters
  const [filters, setFilters] = useState({
    q: '', category: '', experience: '', location: '', is_remote: '', sort: 'posted_date',
  });
  const [filterOptions, setFilterOptions] = useState({});
  const [mobileFilters, setMobileFilters] = useState(false);

  // Search debounce
  const [searchTimer, setSearchTimer] = useState(null);

  useEffect(() => {
    fetchUser();
    loadFilterOptions();
  }, []);

  useEffect(() => {
    if (tab === 'recommended') {
      loadRecommended();
    } else {
      setOffset(0);
      loadAllJobs(0);
    }
  }, [tab]);

  // Reload all jobs when filters change (debounced for search)
  useEffect(() => {
    if (tab !== 'all') return;
    if (searchTimer) clearTimeout(searchTimer);
    const timer = setTimeout(() => {
      setOffset(0);
      loadAllJobs(0);
    }, filters.q ? 400 : 0);
    setSearchTimer(timer);
    return () => clearTimeout(timer);
  }, [filters.q, filters.category, filters.experience, filters.location, filters.is_remote, filters.sort]);

  const loadFilterOptions = async () => {
    try {
      const { data } = await api.get('/jobs/filters/');
      setFilterOptions(data);
    } catch { /* ignore */ }
  };

  const loadRecommended = async () => {
    setLoading(true);
    try {
      const { data } = await api.get('/jobs/recommended/', { params: { limit: 30 } });
      setRecommended(data.jobs || []);
      setRecTotal(data.total || 0);
    } catch { /* ignore */ }
    setLoading(false);
  };

  const loadAllJobs = async (off) => {
    if (off === 0) setLoading(true);
    else setLoadingMore(true);
    try {
      const params = { ...filters, limit: 20, offset: off };
      const { data } = await api.get('/jobs/', { params });
      if (off === 0) {
        setAllJobs(data.jobs || []);
      } else {
        setAllJobs((prev) => [...prev, ...(data.jobs || [])]);
      }
      setAllTotal(data.total || 0);
    } catch { /* ignore */ }
    setLoading(false);
    setLoadingMore(false);
  };

  const loadMore = () => {
    const newOffset = offset + 20;
    setOffset(newOffset);
    loadAllJobs(newOffset);
  };

  const updateFilter = (key, val) => {
    setFilters((f) => ({ ...f, [key]: val }));
  };

  const clearFilters = () => {
    setFilters({ q: '', category: '', experience: '', location: '', is_remote: '', sort: 'posted_date' });
  };

  const currentUser = useAuthStore.getState().user || user;
  const jobs = tab === 'recommended' ? recommended : allJobs;
  const total = tab === 'recommended' ? recTotal : allTotal;

  return (
    <DashboardLayout user={currentUser}>
      {/* Page header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-1">
          <div className="w-10 h-10 bg-gradient-to-br from-primary-100 to-primary-200 rounded-xl flex items-center justify-center">
            <Briefcase className="w-5 h-5 text-primary-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Jobs</h1>
            <p className="text-sm text-gray-400">
              {total > 0 ? `${total} jobs found` : 'Discover jobs matching your skills'}
            </p>
          </div>
        </div>
      </div>

      {/* Tab toggle */}
      <div className="flex items-center gap-3 mb-6">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-1.5 inline-flex gap-1">
          <button
            onClick={() => setTab('recommended')}
            className={`px-5 py-2.5 rounded-xl text-sm font-semibold border-none cursor-pointer transition-all ${
              tab === 'recommended'
                ? 'bg-primary-600 text-white shadow-sm shadow-primary-600/20'
                : 'bg-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'
            }`}
          >
            For You
          </button>
          <button
            onClick={() => setTab('all')}
            className={`px-5 py-2.5 rounded-xl text-sm font-semibold border-none cursor-pointer transition-all ${
              tab === 'all'
                ? 'bg-primary-600 text-white shadow-sm shadow-primary-600/20'
                : 'bg-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'
            }`}
          >
            All Jobs
          </button>
        </div>

        {/* Mobile filter toggle */}
        {tab === 'all' && (
          <button
            onClick={() => setMobileFilters(!mobileFilters)}
            className="lg:hidden flex items-center gap-1.5 px-3 py-2 bg-gray-100 text-gray-600 rounded-xl text-sm font-medium
              border-none cursor-pointer hover:bg-gray-200 transition-colors"
          >
            <Filter className="w-4 h-4" />
            Filters
          </button>
        )}
      </div>

      {/* Layout: main + filters sidebar */}
      <div className="flex gap-6">
        {/* Main jobs list */}
        <div className="flex-1 min-w-0">
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="w-7 h-7 text-primary-500 animate-spin" />
            </div>
          ) : jobs.length === 0 ? (
            <div className="bg-white rounded-2xl border border-gray-100 p-10 text-center">
              <Briefcase className="w-10 h-10 text-gray-300 mx-auto mb-3" />
              <p className="text-sm text-gray-500">
                {tab === 'recommended'
                  ? 'No matching jobs found. Add more skills to your profile for better recommendations.'
                  : 'No jobs found matching your filters. Try adjusting your search criteria.'}
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {jobs.map((job) => (
                <JobCard
                  key={job.job_id}
                  job={job}
                  showMatch={tab === 'recommended'}
                />
              ))}

              {/* Load more */}
              {tab === 'all' && allJobs.length < allTotal && (
                <div className="text-center pt-4">
                  <button
                    onClick={loadMore}
                    disabled={loadingMore}
                    className="h-10 px-6 bg-white text-primary-600 border border-primary-200 rounded-xl text-sm font-semibold
                      cursor-pointer hover:bg-primary-50 disabled:opacity-60 transition-all"
                  >
                    {loadingMore ? 'Loading...' : `Load more (${allTotal - allJobs.length} remaining)`}
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Filters sidebar — desktop always, mobile overlay */}
        {tab === 'all' && (
          <>
            {/* Desktop */}
            <div className="hidden lg:block w-[260px] flex-shrink-0">
              <div className="sticky top-6">
                <FiltersPanel
                  filters={filters}
                  filterOptions={filterOptions}
                  onChange={updateFilter}
                  onClear={clearFilters}
                />
              </div>
            </div>

            {/* Mobile overlay */}
            {mobileFilters && (
              <div className="fixed inset-0 z-40 lg:hidden">
                <div className="fixed inset-0 bg-black/30" onClick={() => setMobileFilters(false)} />
                <div className="fixed inset-y-0 right-0 w-[300px] bg-gray-50 shadow-xl z-50 overflow-y-auto p-4">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-bold text-gray-800">Filters</h3>
                    <button
                      onClick={() => setMobileFilters(false)}
                      className="p-1 text-gray-400 hover:text-gray-600 bg-transparent border-none cursor-pointer"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </div>
                  <FiltersPanel
                    filters={filters}
                    filterOptions={filterOptions}
                    onChange={updateFilter}
                    onClear={clearFilters}
                  />
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </DashboardLayout>
  );
}
