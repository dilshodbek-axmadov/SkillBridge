import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  Map, Target, Clock, CheckCircle2, Circle, Lock, Play, BookOpen,
  Sparkles, ArrowRight, ChevronDown, ChevronUp, ExternalLink,
  X, Star, Video, FileText, Code2, GraduationCap, Globe,
  Loader2, AlertTriangle, RefreshCw, Brain, Zap, TrendingUp,
  CircleDot, RotateCcw,
} from 'lucide-react';
import DashboardLayout from '../components/layout/DashboardLayout';
import useAuthStore from '../store/authStore';
import api from '../services/api';

/* ──────────────────────────── helpers ──────────────────────────── */

const PRIORITY_STYLES = {
  high:   { bg: 'bg-red-50',    text: 'text-red-700',    border: 'border-red-200',   dot: 'bg-red-500' },
  medium: { bg: 'bg-amber-50',  text: 'text-amber-700',  border: 'border-amber-200', dot: 'bg-amber-500' },
  low:    { bg: 'bg-blue-50',   text: 'text-blue-700',   border: 'border-blue-200',  dot: 'bg-blue-500' },
};

const STATUS_CONFIG = {
  completed:   { label: 'Completed',   color: 'text-emerald-600', bg: 'bg-emerald-50',  border: 'border-emerald-200', icon: CheckCircle2 },
  in_progress: { label: 'In Progress', color: 'text-primary-600', bg: 'bg-primary-50',  border: 'border-primary-200', icon: Play },
  pending:     { label: 'Pending',     color: 'text-gray-500',    bg: 'bg-gray-50',     border: 'border-gray-200',    icon: Circle },
  skipped:     { label: 'Skipped',     color: 'text-gray-400',    bg: 'bg-gray-50',     border: 'border-gray-200',    icon: Circle },
};

const RESOURCE_ICONS = {
  video:         Video,
  tutorial:      Code2,
  documentation: FileText,
  article:       FileText,
  interactive:   Globe,
  book:          BookOpen,
  practice:      Code2,
};

const DIFFICULTY_COLORS = {
  beginner:     { bg: 'bg-emerald-50',  text: 'text-emerald-700', border: 'border-emerald-200' },
  intermediate: { bg: 'bg-blue-50',     text: 'text-blue-700',    border: 'border-blue-200' },
  advanced:     { bg: 'bg-purple-50',   text: 'text-purple-700',  border: 'border-purple-200' },
  expert:       { bg: 'bg-red-50',      text: 'text-red-700',     border: 'border-red-200' },
};

function formatHours(h) {
  if (!h) return '0h';
  if (h < 1) return `${Math.round(h * 60)}m`;
  return `${h}h`;
}

/* ──────────────────────────── stat card ──────────────────────────── */

function StatCard({ icon: Icon, label, value, sub, color = 'primary' }) {
  const colors = {
    primary: 'from-primary-500 to-primary-600',
    emerald: 'from-emerald-500 to-emerald-600',
    amber:   'from-amber-500 to-amber-600',
    purple:  'from-purple-500 to-purple-600',
  };
  return (
    <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-4 flex items-center gap-4">
      <div className={`w-11 h-11 bg-gradient-to-br ${colors[color]} rounded-xl flex items-center justify-center flex-shrink-0`}>
        <Icon className="w-5 h-5 text-white" />
      </div>
      <div className="min-w-0">
        <p className="text-lg font-bold text-gray-900 dark:text-gray-100 leading-tight">{value}</p>
        <p className="text-xs text-gray-500 dark:text-gray-400 dark:text-gray-500">{label}</p>
        {sub && <p className="text-[10px] text-gray-400 dark:text-gray-500 mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}

/* ──────────────── circular progress ──────────────── */

function CircularProgress({ percentage, size = 48 }) {
  const r = (size - 6) / 2;
  const c = 2 * Math.PI * r;
  const offset = c - (percentage / 100) * c;
  return (
    <svg width={size} height={size} className="transform -rotate-90">
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#e5e7eb" strokeWidth={5} />
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#7c3aed" strokeWidth={5}
        strokeDasharray={c} strokeDashoffset={offset} strokeLinecap="round"
        className="transition-all duration-700"
      />
    </svg>
  );
}

/* ──────────────── timeline node ──────────────── */

function TimelineNode({ item, index, total, onStatusChange, onViewResources, isUpdating }) {
  const status = STATUS_CONFIG[item.status] || STATUS_CONFIG.pending;
  const priority = PRIORITY_STYLES[item.priority] || PRIORITY_STYLES.medium;
  const StatusIcon = status.icon;
  const isLast = index === total - 1;
  const isCompleted = item.status === 'completed';
  const isInProgress = item.status === 'in_progress';

  return (
    <div className="flex gap-4 relative">
      {/* timeline line + circle */}
      <div className="flex flex-col items-center flex-shrink-0 w-10">
        {/* circle */}
        <div className={`w-10 h-10 rounded-full flex items-center justify-center border-2 z-10 transition-all ${
          isCompleted
            ? 'bg-emerald-500 border-emerald-500'
            : isInProgress
              ? 'bg-primary-500 border-primary-500 ring-4 ring-primary-100'
              : 'bg-white border-gray-300'
        }`}>
          {isCompleted ? (
            <CheckCircle2 className="w-5 h-5 text-white" />
          ) : isInProgress ? (
            <Play className="w-4 h-4 text-white ml-0.5" />
          ) : (
            <span className="text-xs font-bold text-gray-400 dark:text-gray-500">{index + 1}</span>
          )}
        </div>
        {/* connector line */}
        {!isLast && (
          <div className={`w-0.5 flex-1 mt-0 ${isCompleted ? 'bg-emerald-300' : 'bg-gray-200'}`} />
        )}
      </div>

      {/* card */}
      <div className={`flex-1 mb-6 rounded-2xl border transition-all ${
        isCompleted
          ? 'bg-emerald-50/50 border-emerald-200'
          : isInProgress
            ? 'bg-white border-primary-200 shadow-sm shadow-primary-100'
            : 'bg-white border-gray-200'
      }`}>
        <div className="p-4 sm:p-5">
          {/* top badges */}
          <div className="flex items-center gap-2 flex-wrap mb-2">
            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold ${status.bg} ${status.color} ${status.border} border`}>
              <StatusIcon className="w-3 h-3" />
              {status.label}
            </span>
            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold ${priority.bg} ${priority.text} ${priority.border} border`}>
              {item.priority}
            </span>
            <span className="text-[11px] text-gray-400 ml-auto">#{index + 1}</span>
          </div>

          {/* skill name */}
          <h3 className={`text-base font-bold mb-1.5 ${isCompleted ? 'text-emerald-800' : 'text-gray-900'}`}>
            {item.skill_name}
          </h3>

          {/* category + duration */}
          <div className="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400 mb-3">
            {item.category && (
              <span className="capitalize">{item.category.replace(/_/g, ' ')}</span>
            )}
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {formatHours(item.estimated_duration_hours)}
            </span>
          </div>

          {/* notes / reason */}
          {item.notes && (
            <p className={`text-xs leading-relaxed mb-3 ${isCompleted ? 'text-emerald-700/70' : 'text-gray-500'}`}>
              {item.notes}
            </p>
          )}

          {/* completed date */}
          {isCompleted && item.completed_at && (
            <p className="text-[11px] text-emerald-600 mb-3">
              Completed on {new Date(item.completed_at).toLocaleDateString()}
            </p>
          )}

          {/* action buttons */}
          <div className="flex items-center gap-2 flex-wrap">
            {isCompleted ? (
              <>
                <button
                  onClick={() => onViewResources(item)}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-emerald-700 bg-emerald-100 rounded-lg border-none cursor-pointer hover:bg-emerald-200 transition-colors"
                >
                  <BookOpen className="w-3.5 h-3.5" /> Review
                </button>
                <button
                  onClick={() => onStatusChange(item.item_id, 'pending')}
                  disabled={isUpdating === item.item_id}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-500 bg-gray-100 dark:bg-gray-800 rounded-lg border-none cursor-pointer hover:bg-gray-200 transition-colors disabled:opacity-50"
                >
                  <RotateCcw className="w-3 h-3" /> Undo
                </button>
              </>
            ) : isInProgress ? (
              <>
                <button
                  onClick={() => onViewResources(item)}
                  className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-white bg-primary-600 rounded-lg border-none cursor-pointer hover:bg-primary-700 transition-colors"
                >
                  <BookOpen className="w-3.5 h-3.5" /> View Resources
                </button>
                <button
                  onClick={() => onStatusChange(item.item_id, 'completed')}
                  disabled={isUpdating === item.item_id}
                  className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-emerald-700 bg-emerald-100 rounded-lg border-none cursor-pointer hover:bg-emerald-200 transition-colors disabled:opacity-50"
                >
                  {isUpdating === item.item_id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle2 className="w-3.5 h-3.5" />}
                  Mark Complete
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={() => onStatusChange(item.item_id, 'in_progress')}
                  disabled={isUpdating === item.item_id}
                  className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-primary-700 bg-primary-50 rounded-lg border border-primary-200 cursor-pointer hover:bg-primary-100 transition-colors disabled:opacity-50"
                >
                  {isUpdating === item.item_id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
                  Start Learning
                </button>
                <button
                  onClick={() => onViewResources(item)}
                  className="flex items-center gap-1.5 px-3 py-2 text-xs font-medium text-gray-600 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 cursor-pointer hover:bg-gray-100 transition-colors"
                >
                  <BookOpen className="w-3.5 h-3.5" /> Preview Resources
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ──────────────── resource panel (slide-over) ──────────────── */

function ResourcePanel({ item, onClose }) {
  const [resources, setResources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [progressMap, setProgressMap] = useState({});

  useEffect(() => {
    if (!item) return;
    setLoading(true);
    setError(null);
    api.get(`/resources/skill/${item.skill_id}/`, { params: { language: 'en', generate_if_missing: true, limit: 20 } })
      .then(r => {
        setResources(r.data.resources || []);
        const pm = {};
        (r.data.resources || []).forEach(res => {
          if (res.user_progress) pm[res.resource_id] = res.user_progress;
        });
        setProgressMap(pm);
      })
      .catch(() => setError('Failed to load resources'))
      .finally(() => setLoading(false));
  }, [item]);

  const handleStartResource = async (resourceId) => {
    try {
      await api.post(`/resources/${resourceId}/start/`);
      setProgressMap(prev => ({ ...prev, [resourceId]: { status: 'started', progress_percentage: 0 } }));
    } catch { /* ignore */ }
  };

  const handleCompleteResource = async (resourceId) => {
    try {
      await api.put(`/resources/${resourceId}/progress/`, { status: 'completed', progress_percentage: 100 });
      setProgressMap(prev => ({ ...prev, [resourceId]: { ...prev[resourceId], status: 'completed', progress_percentage: 100 } }));
    } catch { /* ignore */ }
  };

  if (!item) return null;

  // group resources by type
  const grouped = {};
  resources.forEach(r => {
    const type = r.resource_type || 'other';
    if (!grouped[type]) grouped[type] = [];
    grouped[type].push(r);
  });

  const typeLabels = {
    video: 'Video Tutorials',
    tutorial: 'Tutorials & Guides',
    documentation: 'Documentation',
    article: 'Articles',
    interactive: 'Interactive Platforms',
    book: 'Books',
    practice: 'Practice Projects',
  };

  const typeOrder = ['video', 'tutorial', 'documentation', 'interactive', 'article', 'practice', 'book'];

  return (
    <>
      {/* backdrop */}
      <div className="fixed inset-0 bg-black/30 z-40" onClick={onClose} />

      {/* panel */}
      <div className="fixed inset-y-0 right-0 w-full sm:w-[520px] bg-white shadow-2xl z-50 flex flex-col overflow-hidden">
        {/* header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200 bg-gradient-to-r from-primary-50 to-purple-50">
          <div className="min-w-0">
            <p className="text-xs text-primary-600 font-medium mb-0.5">Learning Resources</p>
            <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100 truncate">{item.skill_name}</h2>
            {item.category && (
              <p className="text-xs text-gray-500 capitalize mt-0.5">{item.category.replace(/_/g, ' ')}</p>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 bg-white rounded-lg border border-gray-200 cursor-pointer transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* body */}
        <div className="flex-1 overflow-y-auto px-5 py-5 space-y-6">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-16 gap-3">
              <div className="relative">
                <Brain className="w-10 h-10 text-primary-400 animate-pulse" />
                <Sparkles className="w-4 h-4 text-purple-500 absolute -top-1 -right-1 animate-bounce" />
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-400 dark:text-gray-500">AI is finding resources for {item.skill_name}...</p>
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <AlertTriangle className="w-8 h-8 text-amber-400 mx-auto mb-2" />
              <p className="text-sm text-gray-500 dark:text-gray-400 dark:text-gray-500">{error}</p>
            </div>
          ) : resources.length === 0 ? (
            <div className="text-center py-12">
              <BookOpen className="w-8 h-8 text-gray-300 mx-auto mb-2" />
              <p className="text-sm text-gray-500 dark:text-gray-400 dark:text-gray-500">No resources available yet for this skill.</p>
            </div>
          ) : (
            <>
              {/* estimated time card */}
              <div className="bg-gradient-to-r from-purple-50 to-primary-50 rounded-xl p-4 border border-purple-100">
                <div className="flex items-center gap-2 mb-2">
                  <Sparkles className="w-4 h-4 text-purple-600" />
                  <h3 className="text-sm font-semibold text-purple-900">Learning Path for {item.skill_name}</h3>
                </div>
                <p className="text-xs text-purple-700/80">
                  Estimated {formatHours(item.estimated_duration_hours)} of learning. Complete the resources below to master this skill.
                </p>
                <div className="flex items-center gap-4 mt-3 text-xs text-purple-600">
                  <span className="flex items-center gap-1"><BookOpen className="w-3 h-3" /> {resources.length} resources</span>
                  <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {formatHours(item.estimated_duration_hours)}</span>
                </div>
              </div>

              {/* grouped resources */}
              {typeOrder.filter(t => grouped[t]).map(type => (
                <div key={type}>
                  <h3 className="text-sm font-semibold text-gray-800 mb-3 flex items-center gap-2">
                    {(() => { const I = RESOURCE_ICONS[type] || FileText; return <I className="w-4 h-4 text-gray-400 dark:text-gray-500" />; })()}
                    {typeLabels[type] || type}
                    <span className="text-xs font-normal text-gray-400 dark:text-gray-500">({grouped[type].length})</span>
                  </h3>
                  <div className="space-y-2.5">
                    {grouped[type].map(res => {
                      const prog = progressMap[res.resource_id];
                      const isCompleted = prog?.status === 'completed';
                      const isStarted = prog && prog.status !== 'completed';
                      const diff = DIFFICULTY_COLORS[res.difficulty_level] || DIFFICULTY_COLORS.beginner;
                      return (
                        <div key={res.resource_id} className={`rounded-xl border p-3.5 transition-all ${isCompleted ? 'bg-emerald-50/50 border-emerald-200' : 'bg-white border-gray-200 hover:border-gray-300 hover:shadow-sm'}`}>
                          <div className="flex items-start gap-3">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 flex-wrap mb-1">
                                <span className={`inline-flex px-1.5 py-0.5 rounded text-[10px] font-semibold ${diff.bg} ${diff.text} border ${diff.border}`}>
                                  {res.difficulty_level}
                                </span>
                                {res.is_free && (
                                  <span className="inline-flex px-1.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                                    Free
                                  </span>
                                )}
                                {res.is_verified && (
                                  <span className="inline-flex px-1.5 py-0.5 rounded text-[10px] font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                                    Verified
                                  </span>
                                )}
                                {res.estimated_duration > 0 && (
                                  <span className="text-[10px] text-gray-400 flex items-center gap-0.5">
                                    <Clock className="w-2.5 h-2.5" /> {formatHours(res.estimated_duration)}
                                  </span>
                                )}
                              </div>
                              <h4 className={`text-sm font-medium leading-snug ${isCompleted ? 'text-emerald-800 line-through' : 'text-gray-900'}`}>
                                {res.title}
                              </h4>
                              {(res.author || res.platform) && (
                                <p className="text-[11px] text-gray-400 dark:text-gray-500 mt-0.5">
                                  {res.author}{res.author && res.platform && ' · '}{res.platform}
                                </p>
                              )}
                              {res.description && (
                                <p className="text-xs text-gray-500 dark:text-gray-400 dark:text-gray-500 mt-1 line-clamp-2">{res.description}</p>
                              )}
                              {res.rating > 0 && (
                                <div className="flex items-center gap-1 mt-1">
                                  <Star className="w-3 h-3 text-amber-400 fill-amber-400" />
                                  <span className="text-[11px] text-gray-500 dark:text-gray-400 dark:text-gray-500">{res.rating.toFixed(1)}</span>
                                </div>
                              )}
                            </div>
                            {/* actions */}
                            <div className="flex flex-col gap-1.5 flex-shrink-0">
                              {res.url && (
                                <a
                                  href={res.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="flex items-center gap-1 px-2.5 py-1.5 text-[11px] font-medium text-primary-700 bg-primary-50 rounded-lg no-underline hover:bg-primary-100 transition-colors border border-primary-200"
                                >
                                  <ExternalLink className="w-3 h-3" /> Open
                                </a>
                              )}
                              {isCompleted ? (
                                <span className="flex items-center gap-1 px-2.5 py-1.5 text-[11px] font-medium text-emerald-700 bg-emerald-100 rounded-lg">
                                  <CheckCircle2 className="w-3 h-3" /> Done
                                </span>
                              ) : isStarted ? (
                                <button
                                  onClick={() => handleCompleteResource(res.resource_id)}
                                  className="flex items-center gap-1 px-2.5 py-1.5 text-[11px] font-medium text-emerald-700 bg-emerald-50 rounded-lg border border-emerald-200 cursor-pointer hover:bg-emerald-100 transition-colors"
                                >
                                  <CheckCircle2 className="w-3 h-3" /> Done
                                </button>
                              ) : (
                                <button
                                  onClick={() => handleStartResource(res.resource_id)}
                                  className="flex items-center gap-1 px-2.5 py-1.5 text-[11px] font-medium text-gray-600 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 cursor-pointer hover:bg-gray-100 transition-colors"
                                >
                                  <Play className="w-3 h-3" /> Start
                                </button>
                              )}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </>
          )}
        </div>
      </div>
    </>
  );
}

/* ──────────────── generating phase ──────────────── */

const PROGRESS_STEPS = [
  { icon: Brain,       text: 'Analyzing your skill gaps...' },
  { icon: Target,      text: 'Mapping career requirements...' },
  { icon: TrendingUp,  text: 'Optimizing learning sequence...' },
  { icon: Sparkles,    text: 'Generating personalized roadmap...' },
];

function GeneratingPhase() {
  const [step, setStep] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setStep(s => (s + 1) % PROGRESS_STEPS.length), 2500);
    return () => clearInterval(t);
  }, []);
  const current = PROGRESS_STEPS[step];
  const Icon = current.icon;

  return (
    <div className="flex flex-col items-center justify-center py-20 gap-6">
      <div className="relative">
        <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-primary-100 to-purple-100 flex items-center justify-center">
          <Brain className="w-10 h-10 text-primary-600 animate-pulse" />
        </div>
        {[0, 1, 2].map(i => (
          <div key={i} className="absolute w-3 h-3 rounded-full bg-purple-400 animate-ping"
            style={{
              top: `${10 + i * 25}%`,
              left: i % 2 === 0 ? '-12px' : 'calc(100% + 4px)',
              animationDelay: `${i * 0.5}s`,
              animationDuration: '2s',
            }}
          />
        ))}
      </div>
      <div className="text-center">
        <div className="flex items-center justify-center gap-2 mb-2">
          <Icon className="w-5 h-5 text-primary-600" />
          <p className="text-sm font-medium text-gray-700">{current.text}</p>
        </div>
        <div className="flex gap-1.5 justify-center mt-4">
          {PROGRESS_STEPS.map((_, i) => (
            <div key={i} className={`h-1.5 rounded-full transition-all duration-300 ${i === step ? 'w-6 bg-primary-500' : 'w-1.5 bg-gray-300'}`} />
          ))}
        </div>
      </div>
    </div>
  );
}

/* ──────────────── empty / no gaps state ──────────────── */

function EmptyState({ hasGaps, onGenerate, generating }) {
  if (!hasGaps) {
    return (
      <div className="text-center py-16">
        <div className="w-16 h-16 bg-amber-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <AlertTriangle className="w-8 h-8 text-amber-400" />
        </div>
        <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-2">No Skill Gaps Found</h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 max-w-md mx-auto mb-6">
          Run a skill gap analysis first to identify what skills you need to learn. The roadmap will be generated based on your skill gaps.
        </p>
        <Link
          to="/skills-gap"
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-primary-600 text-white rounded-xl text-sm font-semibold no-underline hover:bg-primary-700 transition-colors"
        >
          <Target className="w-4 h-4" /> Run Skill Gap Analysis
        </Link>
      </div>
    );
  }

  return (
    <div className="text-center py-16">
      <div className="w-16 h-16 bg-gradient-to-br from-primary-100 to-purple-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
        <Map className="w-8 h-8 text-primary-600" />
      </div>
      <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-2">Generate Your Learning Roadmap</h2>
      <p className="text-sm text-gray-500 dark:text-gray-400 max-w-md mx-auto mb-6">
        AI will create a personalized learning path based on your skill gaps, ordered by priority and dependencies.
      </p>
      <button
        onClick={onGenerate}
        disabled={generating}
        className="inline-flex items-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-xl text-sm font-semibold border-none cursor-pointer hover:bg-primary-700 transition-colors disabled:opacity-50"
      >
        {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
        Generate Roadmap
      </button>
    </div>
  );
}

/* ──────────────── main page ──────────────── */

export default function LearningRoadmapPage() {
  const { user } = useAuthStore();
  const [roadmap, setRoadmap] = useState(null);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState(null);
  const [hasGaps, setHasGaps] = useState(false);
  const [updatingItem, setUpdatingItem] = useState(null);
  const [resourceItem, setResourceItem] = useState(null);
  const [filter, setFilter] = useState('all'); // all, pending, in_progress, completed

  // load existing roadmap
  const loadRoadmap = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // load roadmaps and check gaps in parallel
      const [roadmapsRes, gapsRes] = await Promise.all([
        api.get('/roadmaps/', { params: { active_only: true } }),
        api.get('/skills/gaps/'),
      ]);

      const gapsData = gapsRes.data.gaps || gapsRes.data || [];
      setHasGaps(gapsData.length > 0);

      const roadmaps = roadmapsRes.data.roadmaps || [];
      if (roadmaps.length > 0) {
        // load detail for the most recent active roadmap
        const latest = roadmaps[0];
        const detailRes = await api.get(`/roadmaps/${latest.roadmap_id}/`);
        const detail = detailRes.data.roadmap || detailRes.data;
        setRoadmap(detail);
        setItems(detail.items || []);
      } else {
        setRoadmap(null);
        setItems([]);
      }
    } catch (err) {
      setError('Failed to load roadmap data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadRoadmap(); }, [loadRoadmap]);

  // generate roadmap
  const handleGenerate = async () => {
    try {
      setGenerating(true);
      setError(null);
      const res = await api.post('/roadmaps/generate/', { language: 'en' });
      if (res.data.success) {
        await loadRoadmap();
      } else {
        setError(res.data.error || 'Failed to generate roadmap');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to generate roadmap');
    } finally {
      setGenerating(false);
    }
  };

  // update item status
  const handleStatusChange = async (itemId, newStatus) => {
    setUpdatingItem(itemId);
    try {
      await api.put(`/roadmaps/items/${itemId}/status/`, { status: newStatus });
      // refresh roadmap
      if (roadmap) {
        const detailRes = await api.get(`/roadmaps/${roadmap.roadmap_id}/`);
        const detail = detailRes.data.roadmap || detailRes.data;
        setRoadmap(detail);
        setItems(detail.items || []);
      }
    } catch { /* ignore */ }
    setUpdatingItem(null);
  };

  // compute stats
  const stats = {
    total: items.length,
    completed: items.filter(i => i.status === 'completed').length,
    inProgress: items.filter(i => i.status === 'in_progress').length,
    pending: items.filter(i => i.status === 'pending').length,
    totalHours: items.reduce((s, i) => s + (i.estimated_duration_hours || 0), 0),
    completedHours: items.filter(i => i.status === 'completed').reduce((s, i) => s + (i.estimated_duration_hours || 0), 0),
  };
  const completionPct = stats.total > 0 ? Math.round((stats.completed / stats.total) * 100) : 0;
  const remainingHours = stats.totalHours - stats.completedHours;

  // filter items
  const filteredItems = filter === 'all' ? items : items.filter(i => i.status === filter);

  return (
    <DashboardLayout user={user}>
      {/* page header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Map className="w-6 h-6 text-primary-600" />
            Learning Roadmap
          </h1>
          {roadmap && (
            <p className="text-sm text-gray-500 dark:text-gray-400 dark:text-gray-500 mt-1">
              Target: <span className="font-medium text-gray-700">{roadmap.target_role}</span>
            </p>
          )}
        </div>
        {roadmap && (
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-primary-700 bg-primary-50 rounded-xl border border-primary-200 cursor-pointer hover:bg-primary-100 transition-colors disabled:opacity-50"
          >
            {generating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
            Regenerate
          </button>
        )}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-6 h-6 text-primary-500 animate-spin" />
        </div>
      ) : generating ? (
        <GeneratingPhase />
      ) : error && !roadmap ? (
        <div className="text-center py-16">
          <AlertTriangle className="w-8 h-8 text-red-400 mx-auto mb-2" />
          <p className="text-sm text-red-600">{error}</p>
          <button onClick={loadRoadmap} className="mt-4 px-4 py-2 text-sm font-medium text-primary-600 bg-primary-50 rounded-lg border border-primary-200 cursor-pointer hover:bg-primary-100 transition-colors">
            Try Again
          </button>
        </div>
      ) : !roadmap ? (
        <EmptyState hasGaps={hasGaps} onGenerate={handleGenerate} generating={generating} />
      ) : (
        <>
          {/* stats bar */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
            <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-4 flex items-center gap-4">
              <div className="relative flex-shrink-0">
                <CircularProgress percentage={completionPct} size={48} />
                <span className="absolute inset-0 flex items-center justify-center text-xs font-bold text-purple-700">
                  {completionPct}%
                </span>
              </div>
              <div>
                <p className="text-lg font-bold text-gray-900 dark:text-gray-100">{completionPct}%</p>
                <p className="text-xs text-gray-500 dark:text-gray-400 dark:text-gray-500">Complete</p>
              </div>
            </div>
            <StatCard icon={CheckCircle2} label="Skills Learned" value={`${stats.completed}/${stats.total}`} color="emerald" />
            <StatCard icon={Clock} label="Hours Remaining" value={formatHours(remainingHours)} sub={`${formatHours(stats.totalHours)} total`} color="amber" />
            <StatCard icon={Target} label="Target Role" value={roadmap.target_role?.length > 18 ? roadmap.target_role.substring(0, 18) + '...' : roadmap.target_role} color="purple" />
          </div>

          {/* error banner */}
          {error && (
            <div className="mb-4 px-4 py-3 bg-red-50 dark:bg-red-900/20 border border-red-200 rounded-xl text-sm text-red-700">
              {error}
            </div>
          )}

          {/* filter bar */}
          <div className="flex items-center gap-2 mb-5 flex-wrap">
            {[
              { key: 'all', label: 'All', count: stats.total },
              { key: 'pending', label: 'Pending', count: stats.pending },
              { key: 'in_progress', label: 'In Progress', count: stats.inProgress },
              { key: 'completed', label: 'Completed', count: stats.completed },
            ].map(f => (
              <button
                key={f.key}
                onClick={() => setFilter(f.key)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium border cursor-pointer transition-colors ${
                  filter === f.key
                    ? 'bg-primary-50 text-primary-700 border-primary-200'
                    : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'
                }`}
              >
                {f.label} ({f.count})
              </button>
            ))}
          </div>

          {/* description */}
          {roadmap.description && (
            <div className="bg-gradient-to-r from-purple-50 to-primary-50 rounded-2xl p-4 mb-6 border border-purple-100">
              <div className="flex items-center gap-2 mb-1.5">
                <Sparkles className="w-4 h-4 text-purple-600" />
                <h3 className="text-sm font-semibold text-purple-900">AI Roadmap Summary</h3>
              </div>
              <p className="text-xs text-purple-800/80 leading-relaxed">{roadmap.description}</p>
            </div>
          )}

          {/* timeline */}
          <div className="max-w-2xl">
            {filteredItems.length === 0 ? (
              <div className="text-center py-12 text-sm text-gray-500 dark:text-gray-400 dark:text-gray-500">
                No skills match the selected filter.
              </div>
            ) : (
              filteredItems.map((item, idx) => (
                <TimelineNode
                  key={item.item_id}
                  item={item}
                  index={idx}
                  total={filteredItems.length}
                  onStatusChange={handleStatusChange}
                  onViewResources={setResourceItem}
                  isUpdating={updatingItem}
                />
              ))
            )}
          </div>
        </>
      )}

      {/* resource slide-over */}
      {resourceItem && (
        <ResourcePanel item={resourceItem} onClose={() => setResourceItem(null)} />
      )}
    </DashboardLayout>
  );
}
