import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import {
  BarChart3, Sparkles, AlertTriangle, Target, BookOpen,
  ArrowRight, RefreshCw, CheckCircle2, XCircle, Clock,
  Loader2, AlertCircle, Brain, ChevronDown, Filter,
  TrendingUp, Zap, Shield, SkipForward, Play,
} from 'lucide-react';
import DashboardLayout from '../components/layout/DashboardLayout';
import useAuthStore from '../store/authStore';
import api from '../services/api';

/* ─── colour maps ──────────────────────────────────── */
const PRIORITY = {
  high:   { badge: 'bg-red-100 text-red-700',    border: 'border-l-red-500',    dot: 'bg-red-500' },
  medium: { badge: 'bg-orange-100 text-orange-700', border: 'border-l-orange-500', dot: 'bg-orange-500' },
  low:    { badge: 'bg-blue-100 text-blue-700',   border: 'border-l-blue-500',   dot: 'bg-blue-500' },
};
const IMPORTANCE = {
  core:      { badge: 'bg-purple-100 text-purple-700', icon: Shield },
  secondary: { badge: 'bg-gray-100 text-gray-600',     icon: Zap },
};
const STATUS_ICON = {
  pending:   Clock,
  learning:  BookOpen,
  completed: CheckCircle2,
  skipped:   SkipForward,
};
const PROFICIENCY_COLORS = {
  expert:       'bg-emerald-100 text-emerald-700',
  advanced:     'bg-blue-100 text-blue-700',
  intermediate: 'bg-amber-100 text-amber-700',
  beginner:     'bg-gray-100 text-gray-600',
};

/* ─── loading messages ──────────────────────────────── */
const LOADING_STEPS = [
  { icon: Brain,       text: 'Reviewing your skills...',          color: 'text-purple-500' },
  { icon: TrendingUp,  text: 'Analyzing market demand...',        color: 'text-blue-500' },
  { icon: Target,      text: 'Identifying skill gaps...',         color: 'text-amber-500' },
  { icon: Sparkles,    text: 'Generating recommendations...',     color: 'text-emerald-500' },
];

/* ─── main page ──────────────────────────────────────── */
export default function SkillGapPage() {
  const { user, fetchUser } = useAuthStore();

  // data
  const [skills, setSkills] = useState([]);
  const [profile, setProfile] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [gaps, setGaps] = useState([]);
  const [byStatus, setByStatus] = useState({});

  // ui
  const [phase, setPhase] = useState('loading');  // loading | confirm | analyzing | results
  const [pageLoading, setPageLoading] = useState(true);
  const [error, setError] = useState('');
  const [loadingStep, setLoadingStep] = useState(0);

  // re-analyze confirmation
  const [showReanalyzeModal, setShowReanalyzeModal] = useState(false);
  const [clearing, setClearing] = useState(false);

  // filters
  const [filterPriority, setFilterPriority] = useState('all');
  const [filterImportance, setFilterImportance] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');

  /* ─── initial load ─────────────────────────── */
  useEffect(() => {
    const load = async () => {
      try {
        if (!user) await fetchUser();

        const [summaryRes, gapsRes] = await Promise.all([
          api.get('/users/profile/summary/'),
          api.get('/skills/gaps/').catch(() => ({ data: { gaps: [], by_status: {} } })),
        ]);

        const summary = summaryRes.data;
        setProfile(summary.profile || {});

        const skillsList = (summary.skills?.list || []).map((s) => ({
          user_skill_id: s.user_skill_id,
          skill_name: s.name_en,
          category: s.category,
          proficiency_level: s.proficiency,
          is_primary: s.is_primary,
        }));
        setSkills(skillsList);

        const gapData = gapsRes.data;
        setGaps(gapData.gaps || []);
        setByStatus(gapData.by_status || {});

        // if user already has gaps, show results directly
        if ((gapData.gaps || []).length > 0) {
          setPhase('results');
        } else {
          setPhase('confirm');
        }
      } catch (err) {
        if (err.response?.status === 401) {
          window.location.href = '/login?redirect=/skills-gap';
          return;
        }
        setError('Failed to load data.');
      } finally {
        setPageLoading(false);
      }
    };
    load();
  }, []);

  /* ─── loading step animation ──────────────── */
  const stepInterval = useRef(null);
  useEffect(() => {
    if (phase === 'analyzing') {
      setLoadingStep(0);
      stepInterval.current = setInterval(() => {
        setLoadingStep((prev) => (prev + 1) % LOADING_STEPS.length);
      }, 2500);
    }
    return () => clearInterval(stepInterval.current);
  }, [phase]);

  /* ─── run analysis ─────────────────────────── */
  const runAnalysis = async () => {
    setPhase('analyzing');
    setError('');
    try {
      const { data } = await api.post('/skills/analyze-gap/', { language: 'en' });
      setAnalysisResult(data);

      // fetch updated gaps
      const gapsRes = await api.get('/skills/gaps/');
      setGaps(gapsRes.data.gaps || []);
      setByStatus(gapsRes.data.by_status || {});

      setPhase('results');
    } catch (err) {
      setError(err.response?.data?.error || 'Analysis failed. Please try again.');
      setPhase('confirm');
    }
  };

  /* ─── update gap status ─────────────────── */
  const updateGapStatus = async (gapId, newStatus) => {
    try {
      await api.put(`/skills/gaps/${gapId}/status/`, { status: newStatus });
      setGaps((prev) =>
        prev.map((g) => (g.gap_id === gapId ? { ...g, status: newStatus } : g))
      );
      setByStatus((prev) => {
        const updated = { ...prev };
        // find old status
        const old = gaps.find((g) => g.gap_id === gapId);
        if (old) {
          updated[old.status] = Math.max(0, (updated[old.status] || 1) - 1);
          updated[newStatus] = (updated[newStatus] || 0) + 1;
        }
        return updated;
      });
    } catch {
      // silent fail
    }
  };

  /* ─── re-analyze (confirm + clear) ────── */
  const handleReanalyzeConfirm = async () => {
    setClearing(true);
    try {
      await api.post('/skills/gaps/clear/');
      setGaps([]);
      setByStatus({});
      setAnalysisResult(null);
      setShowReanalyzeModal(false);
      setPhase('confirm');
    } catch {
      // silent fail — still go to confirm
      setShowReanalyzeModal(false);
      setPhase('confirm');
    } finally {
      setClearing(false);
    }
  };

  /* ─── filtered gaps ────────────────────── */
  const filtered = gaps.filter((g) => {
    if (filterPriority !== 'all' && g.priority !== filterPriority) return false;
    if (filterImportance !== 'all' && g.importance !== filterImportance) return false;
    if (filterStatus !== 'all' && g.status !== filterStatus) return false;
    return true;
  });

  /* ─── page loading / error states ───────── */
  if (pageLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-10 h-10 text-primary-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-500 dark:text-gray-400 text-sm">Loading...</p>
        </div>
      </div>
    );
  }
  if (error && phase !== 'confirm' && phase !== 'results') {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-10 h-10 text-red-400 mx-auto mb-3" />
          <p className="text-gray-600 dark:text-gray-300">{error}</p>
          <button onClick={() => window.location.reload()} className="mt-4 px-5 py-2 bg-primary-600 text-white rounded-lg text-sm font-semibold border-none cursor-pointer hover:bg-primary-700 transition-colors">
            Retry
          </button>
        </div>
      </div>
    );
  }

  /* ─── render ───────────────────────────── */
  return (
    <DashboardLayout user={user}>
      <div className="space-y-6">

        {/* ── PHASE: CONFIRM SKILLS ── */}
        {phase === 'confirm' && (
          <ConfirmPhase
            skills={skills}
            profile={profile}
            error={error}
            onConfirm={runAnalysis}
          />
        )}

        {/* ── PHASE: ANALYZING ── */}
        {phase === 'analyzing' && (
          <AnalyzingPhase step={loadingStep} />
        )}

        {/* ── PHASE: RESULTS ── */}
        {phase === 'results' && (
          <ResultsPhase
            analysisResult={analysisResult}
            gaps={filtered}
            allGaps={gaps}
            byStatus={byStatus}
            skills={skills}
            filterPriority={filterPriority}
            filterImportance={filterImportance}
            filterStatus={filterStatus}
            onFilterPriority={setFilterPriority}
            onFilterImportance={setFilterImportance}
            onFilterStatus={setFilterStatus}
            onUpdateStatus={updateGapStatus}
            onReanalyze={() => setShowReanalyzeModal(true)}
          />
        )}
      </div>

      {/* Re-analyze confirmation modal */}
      {showReanalyzeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/40" onClick={() => !clearing && setShowReanalyzeModal(false)} />
          <div className="relative bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-2xl shadow-xl max-w-md w-full mx-4 p-6">
            <div className="w-12 h-12 bg-amber-50 rounded-xl flex items-center justify-center mx-auto mb-4">
              <AlertTriangle className="w-6 h-6 text-amber-500" />
            </div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 text-center mb-2">Re-analyze Skills?</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 text-center mb-6">
              This will clear your current gap analysis results. You will need to run a new analysis to see updated recommendations.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowReanalyzeModal(false)}
                disabled={clearing}
                className="flex-1 px-4 py-2.5 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-xl text-sm font-semibold border-none cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleReanalyzeConfirm}
                disabled={clearing}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-primary-600 text-white rounded-xl text-sm font-semibold border-none cursor-pointer hover:bg-primary-700 transition-colors disabled:opacity-50"
              >
                {clearing ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
                {clearing ? 'Clearing...' : 'Yes, Re-analyze'}
              </button>
            </div>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}

/* ═════════════════════════════════════════════════════
   Phase 1 — Confirm Skills
   ═════════════════════════════════════════════════════ */
function ConfirmPhase({ skills, profile, error, onConfirm }) {
  return (
    <div className="max-w-2xl mx-auto space-y-6 py-4">
      {/* header */}
      <div className="text-center">
        <div className="w-16 h-16 bg-gradient-to-br from-primary-500 to-purple-600 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg shadow-primary-500/20">
          <BarChart3 className="w-8 h-8 text-white" />
        </div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Skill Gap Analysis</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-2 max-w-md mx-auto">
          Our AI will analyze your current skills against market demand and identify gaps
          to help you grow your career.
        </p>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 rounded-xl p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* profile summary */}
      {profile && (profile.desired_role || profile.experience_level) && (
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-5">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">Your Profile</h3>
          <div className="flex flex-wrap gap-3">
            {profile.desired_role && (
              <div className="flex items-center gap-2 bg-primary-50 text-primary-700 px-3 py-1.5 rounded-lg text-sm font-medium">
                <Target className="w-3.5 h-3.5" />
                Target: {profile.desired_role}
              </div>
            )}
            {profile.experience_level && (
              <div className="flex items-center gap-2 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 px-3 py-1.5 rounded-lg text-sm font-medium capitalize">
                <TrendingUp className="w-3.5 h-3.5" />
                {profile.experience_level}
              </div>
            )}
          </div>
        </div>
      )}

      {/* current skills */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            Your Current Skills ({skills.length})
          </h3>
          <Link
            to="/manage-skills"
            className="text-xs text-primary-600 font-medium no-underline hover:underline flex items-center gap-1"
          >
            Edit skills <ArrowRight className="w-3 h-3" />
          </Link>
        </div>

        {skills.length === 0 ? (
          <div className="text-center py-8">
            <AlertTriangle className="w-8 h-8 text-amber-400 mx-auto mb-2" />
            <p className="text-sm text-gray-500 dark:text-gray-400">No skills found. Add your skills first for a better analysis.</p>
            <Link
              to="/manage-skills"
              className="inline-block mt-3 px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-semibold no-underline hover:bg-primary-700 transition-colors"
            >
              Add Skills
            </Link>
          </div>
        ) : (
          <div className="flex flex-wrap gap-2">
            {skills.map((s) => {
              const colors = PROFICIENCY_COLORS[s.proficiency_level] || PROFICIENCY_COLORS.beginner;
              return (
                <span
                  key={s.user_skill_id}
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium ${colors}`}
                >
                  {s.skill_name}
                  {s.is_primary && (
                    <span className="w-1.5 h-1.5 bg-current rounded-full opacity-60" />
                  )}
                </span>
              );
            })}
          </div>
        )}
      </div>

      {/* important notice */}
      <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl p-4 flex items-start gap-3">
        <Sparkles className="w-5 h-5 text-amber-500 mt-0.5 flex-shrink-0" />
        <div>
          <p className="text-sm font-medium text-amber-800 dark:text-amber-200">Before we begin</p>
          <p className="text-xs text-amber-700 dark:text-amber-300 mt-1">
            The analysis is based on your current skills listed above. Make sure they are
            up to date for the most accurate results.
          </p>
        </div>
      </div>

      {/* actions */}
      <div className="flex flex-col sm:flex-row gap-3">
        <button
          onClick={onConfirm}
          disabled={skills.length === 0}
          className="flex-1 flex items-center justify-center gap-2 px-6 py-3.5 bg-primary-600 text-white rounded-xl text-sm font-semibold border-none cursor-pointer hover:bg-primary-700 transition-colors disabled:bg-gray-300 dark:disabled:bg-gray-700 disabled:cursor-not-allowed shadow-sm"
        >
          <Sparkles className="w-4 h-4" />
          My skills are up to date — Analyze
        </button>
        <Link
          to="/manage-skills"
          className="flex-1 flex items-center justify-center gap-2 px-6 py-3.5 border border-gray-300 dark:border-gray-700 text-gray-600 dark:text-gray-300 rounded-xl text-sm font-semibold no-underline hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors text-center"
        >
          Update my skills first
        </Link>
      </div>
    </div>
  );
}

/* ═════════════════════════════════════════════════════
   Phase 2 — AI Analyzing
   ═════════════════════════════════════════════════════ */
function AnalyzingPhase({ step }) {
  return (
    <div className="max-w-lg mx-auto py-16">
      <div className="text-center space-y-8">
        {/* animated icon */}
        <div className="relative w-24 h-24 mx-auto">
          <div className="absolute inset-0 bg-gradient-to-br from-primary-400 to-purple-500 rounded-3xl animate-pulse opacity-20" />
          <div className="absolute inset-2 bg-gradient-to-br from-primary-500 to-purple-600 rounded-2xl flex items-center justify-center shadow-lg shadow-primary-500/30">
            <Brain className="w-10 h-10 text-white" />
          </div>
          {/* orbiting dots */}
          <div className="absolute inset-0 animate-spin" style={{ animationDuration: '4s' }}>
            <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1 w-2.5 h-2.5 bg-primary-400 rounded-full" />
          </div>
          <div className="absolute inset-0 animate-spin" style={{ animationDuration: '6s', animationDirection: 'reverse' }}>
            <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1 w-2 h-2 bg-purple-400 rounded-full" />
          </div>
        </div>

        <div>
          <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">Analyzing your skills</h2>
          <p className="text-sm text-gray-500 dark:text-gray-400">This may take a moment...</p>
        </div>

        {/* progress steps */}
        <div className="space-y-3 text-left max-w-xs mx-auto">
          {LOADING_STEPS.map((s, i) => {
            const Icon = s.icon;
            const isActive = i === step;
            const isDone = i < step;
            return (
              <div
                key={i}
                className={`flex items-center gap-3 px-4 py-2.5 rounded-xl transition-all duration-500 ${
                  isActive
                    ? 'bg-white dark:bg-gray-900 shadow-sm border border-gray-200 dark:border-gray-700 scale-[1.02]'
                    : isDone
                      ? 'opacity-50'
                      : 'opacity-30'
                }`}
              >
                {isDone ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                ) : isActive ? (
                  <Icon className={`w-5 h-5 ${s.color} flex-shrink-0 animate-pulse`} />
                ) : (
                  <div className="w-5 h-5 rounded-full border-2 border-gray-200 dark:border-gray-700 flex-shrink-0" />
                )}
                <span className={`text-sm font-medium ${isActive ? 'text-gray-900 dark:text-gray-100' : 'text-gray-500 dark:text-gray-400'}`}>
                  {s.text}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

/* ═════════════════════════════════════════════════════
   Phase 3 — Results
   ═════════════════════════════════════════════════════ */
function ResultsPhase({
  analysisResult,
  gaps,
  allGaps,
  byStatus,
  skills,
  filterPriority,
  filterImportance,
  filterStatus,
  onFilterPriority,
  onFilterImportance,
  onFilterStatus,
  onUpdateStatus,
  onReanalyze,
}) {
  const totalGaps = allGaps.length;
  const coreCount = allGaps.filter((g) => g.importance === 'core').length;
  const highCount = allGaps.filter((g) => g.priority === 'high').length;
  const completedCount = byStatus.completed || 0;

  const summary = analysisResult?.analysis_summary || analysisResult?.summary || null;
  const recommendations = analysisResult?.recommendations || [];

  const stats = [
    { label: 'Total Gaps', value: totalGaps, icon: Target, bg: 'bg-red-50', iconBg: 'bg-red-100', color: 'text-red-600', iconColor: 'text-red-500' },
    { label: 'Core Skills', value: coreCount, icon: Shield, bg: 'bg-purple-50', iconBg: 'bg-purple-100', color: 'text-purple-600', iconColor: 'text-purple-500' },
    { label: 'High Priority', value: highCount, icon: AlertTriangle, bg: 'bg-amber-50', iconBg: 'bg-amber-100', color: 'text-amber-600', iconColor: 'text-amber-500' },
    { label: 'Completed', value: completedCount, icon: CheckCircle2, bg: 'bg-emerald-50', iconBg: 'bg-emerald-100', color: 'text-emerald-600', iconColor: 'text-emerald-500' },
  ];

  return (
    <div className="space-y-6">
      {/* header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">Skill Gap Analysis</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
            {totalGaps} skill{totalGaps !== 1 ? 's' : ''} identified to boost your career
          </p>
        </div>
        <button
          onClick={onReanalyze}
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 rounded-xl text-sm font-medium cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Re-analyze
        </button>
      </div>

      {/* stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((s, i) => {
          const Icon = s.icon;
          return (
            <div key={i} className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5 hover:shadow-md transition-shadow">
              <div className={`w-10 h-10 ${s.iconBg} rounded-lg flex items-center justify-center mb-3`}>
                <Icon className={`w-5 h-5 ${s.iconColor}`} />
              </div>
              <p className={`text-2xl font-bold ${s.color}`}>{s.value}</p>
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400 mt-0.5">{s.label}</p>
            </div>
          );
        })}
      </div>

      {/* AI summary */}
      {summary && (
        <div className="bg-gradient-to-r from-purple-50 to-primary-50 rounded-2xl border border-purple-100 p-6">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="w-4 h-4 text-purple-500" />
            <span className="text-sm font-bold text-purple-700">AI Analysis Summary</span>
          </div>
          <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{summary}</p>

          {recommendations.length > 0 && (
            <div className="mt-4 pt-4 border-t border-purple-100">
              <p className="text-xs font-semibold text-purple-600 uppercase tracking-wide mb-2">Recommendations</p>
              <ul className="space-y-2">
                {recommendations.map((r, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
                    <ArrowRight className="w-3.5 h-3.5 text-purple-400 mt-0.5 flex-shrink-0" />
                    {r}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* filters */}
      <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-4">
        <div className="flex items-center gap-2 mb-3">
          <Filter className="w-4 h-4 text-gray-400 dark:text-gray-500" />
          <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">Filters</span>
        </div>
        <div className="flex flex-wrap gap-3">
          <FilterSelect
            label="Priority"
            value={filterPriority}
            onChange={onFilterPriority}
            options={[
              { value: 'all', label: 'All Priorities' },
              { value: 'high', label: 'High' },
              { value: 'medium', label: 'Medium' },
              { value: 'low', label: 'Low' },
            ]}
          />
          <FilterSelect
            label="Importance"
            value={filterImportance}
            onChange={onFilterImportance}
            options={[
              { value: 'all', label: 'All' },
              { value: 'core', label: 'Core' },
              { value: 'secondary', label: 'Secondary' },
            ]}
          />
          <FilterSelect
            label="Status"
            value={filterStatus}
            onChange={onFilterStatus}
            options={[
              { value: 'all', label: 'All Statuses' },
              { value: 'pending', label: 'Pending' },
              { value: 'learning', label: 'Learning' },
              { value: 'completed', label: 'Completed' },
            ]}
          />
        </div>
      </div>

      {/* gap list */}
      {gaps.length === 0 ? (
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 p-10 text-center">
          <Target className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <p className="text-sm text-gray-500 dark:text-gray-400">No skill gaps match the current filters.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {gaps.map((gap) => (
            <GapCard key={gap.gap_id} gap={gap} onUpdateStatus={onUpdateStatus} />
          ))}
        </div>
      )}
    </div>
  );
}

/* ─── filter select ───────────────────────────────── */
function FilterSelect({ label, value, onChange, options }) {
  return (
    <div className="relative">
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="appearance-none bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 pr-8 text-sm text-gray-700 dark:text-gray-300 font-medium cursor-pointer hover:border-gray-300 dark:hover:border-gray-600 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
      <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400 pointer-events-none" />
    </div>
  );
}

/* ─── gap card ──────────────────────────────────── */
function GapCard({ gap, onUpdateStatus }) {
  const pri = PRIORITY[gap.priority] || PRIORITY.medium;
  const imp = IMPORTANCE[gap.importance] || IMPORTANCE.secondary;
  const ImpIcon = imp.icon;
  const StIcon = STATUS_ICON[gap.status] || Clock;

  const statusLabel = {
    pending: 'Pending',
    learning: 'Learning',
    completed: 'Completed',
    skipped: 'Skipped',
  };

  return (
    <div className={`bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 border-l-4 ${pri.border} p-5 hover:shadow-md transition-shadow`}>
      <div className="flex flex-col sm:flex-row sm:items-start gap-4">
        {/* content */}
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-2">
            <h3 className="text-base font-bold text-gray-900 dark:text-gray-100">{gap.skill_name || gap.skill?.name_en || 'Unknown Skill'}</h3>
            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold uppercase ${pri.badge}`}>
              {gap.priority}
            </span>
            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold uppercase ${imp.badge}`}>
              <ImpIcon className="w-2.5 h-2.5" />
              {gap.importance}
            </span>
          </div>

          {gap.reason && (
            <p className="text-sm text-gray-600 dark:text-gray-300 leading-relaxed mb-3">{gap.reason}</p>
          )}

          {/* current status */}
          <div className="flex items-center gap-1.5 text-xs text-gray-400 dark:text-gray-500">
            <StIcon className="w-3.5 h-3.5" />
            <span className="font-medium">{statusLabel[gap.status] || gap.status}</span>
          </div>
        </div>

        {/* actions */}
        <div className="flex sm:flex-col gap-2 flex-shrink-0">
          {gap.status === 'pending' && (
            <>
              <button
                onClick={() => onUpdateStatus(gap.gap_id, 'learning')}
                className="inline-flex items-center gap-1.5 px-3 py-2 bg-primary-600 text-white rounded-lg text-xs font-semibold border-none cursor-pointer hover:bg-primary-700 transition-colors"
              >
                <Play className="w-3 h-3" />
                Start Learning
              </button>
              <button
                onClick={() => onUpdateStatus(gap.gap_id, 'skipped')}
                className="inline-flex items-center gap-1.5 px-3 py-2 bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-300 rounded-lg text-xs font-semibold border-none cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
              >
                <SkipForward className="w-3 h-3" />
                Skip
              </button>
            </>
          )}
          {gap.status === 'learning' && (
            <button
              onClick={() => onUpdateStatus(gap.gap_id, 'completed')}
              className="inline-flex items-center gap-1.5 px-3 py-2 bg-emerald-600 text-white rounded-lg text-xs font-semibold border-none cursor-pointer hover:bg-emerald-700 transition-colors"
            >
              <CheckCircle2 className="w-3 h-3" />
              Mark Complete
            </button>
          )}
          {gap.status === 'skipped' && (
            <button
              onClick={() => onUpdateStatus(gap.gap_id, 'pending')}
              className="inline-flex items-center gap-1.5 px-3 py-2 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 rounded-lg text-xs font-semibold border-none cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
            >
              <RefreshCw className="w-3 h-3" />
              Restore
            </button>
          )}
          {gap.status === 'completed' && (
            <span className="inline-flex items-center gap-1.5 px-3 py-2 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-300 rounded-lg text-xs font-semibold">
              <CheckCircle2 className="w-3 h-3" />
              Done
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
