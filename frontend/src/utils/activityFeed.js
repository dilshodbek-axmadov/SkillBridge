import {
  Sparkles,
  CheckCircle2,
  FileText,
  Code2,
  Layers,
  Trash2,
  BarChart3,
  RefreshCw,
  Map,
  UserPlus,
} from 'lucide-react';

export function formatRelativeTime(isoString) {
  if (!isoString) return '';
  const then = new Date(isoString).getTime();
  if (Number.isNaN(then)) return '';
  let diffSec = Math.round((Date.now() - then) / 1000);
  if (diffSec < 45) return 'Just now';
  let n = Math.round(diffSec / 60);
  if (n < 60) return `${n}m ago`;
  n = Math.round(diffSec / 3600);
  if (n < 48) return `${n}h ago`;
  n = Math.round(diffSec / 86400);
  if (n < 14) return `${n}d ago`;
  return new Date(isoString).toLocaleDateString();
}

const DEFAULT_STYLE = {
  bg: 'bg-gray-100 dark:bg-gray-800',
  iconClass: 'text-gray-600 dark:text-gray-400',
  Icon: Sparkles,
};

const TYPE_STYLE = {
  account_created: { bg: 'bg-emerald-100 dark:bg-emerald-900/40', iconClass: 'text-emerald-600 dark:text-emerald-400', Icon: UserPlus },
  profile_setup: { bg: 'bg-emerald-100 dark:bg-emerald-900/40', iconClass: 'text-emerald-600 dark:text-emerald-400', Icon: CheckCircle2 },
  cv_uploaded: { bg: 'bg-blue-100 dark:bg-blue-900/40', iconClass: 'text-blue-600 dark:text-blue-400', Icon: FileText },
  skill_added: { bg: 'bg-violet-100 dark:bg-violet-900/40', iconClass: 'text-violet-600 dark:text-violet-400', Icon: Code2 },
  skills_bulk_added: { bg: 'bg-violet-100 dark:bg-violet-900/40', iconClass: 'text-violet-600 dark:text-violet-400', Icon: Layers },
  skill_removed: { bg: 'bg-stone-100 dark:bg-stone-800', iconClass: 'text-stone-600 dark:text-stone-400', Icon: Trash2 },
  gap_analyzed: { bg: 'bg-purple-100 dark:bg-purple-900/40', iconClass: 'text-purple-600 dark:text-purple-400', Icon: BarChart3 },
  gap_status: { bg: 'bg-amber-100 dark:bg-amber-900/40', iconClass: 'text-amber-600 dark:text-amber-400', Icon: RefreshCw },
  gaps_cleared: { bg: 'bg-slate-100 dark:bg-slate-800', iconClass: 'text-slate-600 dark:text-slate-400', Icon: RefreshCw },
  roadmap_created: { bg: 'bg-sky-100 dark:bg-sky-900/40', iconClass: 'text-sky-600 dark:text-sky-400', Icon: Map },
  roadmap_progress: { bg: 'bg-teal-100 dark:bg-teal-900/40', iconClass: 'text-teal-600 dark:text-teal-400', Icon: CheckCircle2 },
};

export function getActivityVisual(activityType) {
  return TYPE_STYLE[activityType] || DEFAULT_STYLE;
}
