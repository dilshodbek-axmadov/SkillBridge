import { useState, useEffect, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Lightbulb, Search, Clock, Target, Filter, X, Loader2,
  ChevronDown, FolderOpen, Sparkles, Github, ExternalLink,
  Play, CheckCircle2, Trash2, Edit3, Plus, BarChart3,
  AlertCircle, Zap, FileText,
} from 'lucide-react';
import DashboardLayout from '../components/layout/DashboardLayout';
import useAuthStore from '../store/authStore';
import api from '../services/api';

/* ── Constants ─────────────────────────────────────────────────── */

const DIFFICULTY_COLORS = {
  beginner:     { bg: 'bg-emerald-100 dark:bg-emerald-900/30', text: 'text-emerald-700 dark:text-emerald-300', border: 'border-emerald-200 dark:border-emerald-800' },
  intermediate: { bg: 'bg-blue-100 dark:bg-blue-900/30',       text: 'text-blue-700 dark:text-blue-300',       border: 'border-blue-200 dark:border-blue-800' },
  advanced:     { bg: 'bg-purple-100 dark:bg-purple-900/30',   text: 'text-purple-700 dark:text-purple-300',   border: 'border-purple-200 dark:border-purple-800' },
};

const STATUS_CONFIG = {
  planned:     { labelKey: 'projectIdeas.status.planned',     icon: '📋', bg: 'bg-gray-100 dark:bg-gray-800',       text: 'text-gray-600 dark:text-gray-400',     progress: 0 },
  in_progress: { labelKey: 'projectIdeas.status.in_progress', icon: '⚙️', bg: 'bg-blue-100 dark:bg-blue-900/30',    text: 'text-blue-700 dark:text-blue-300',     progress: 50 },
  completed:   { labelKey: 'projectIdeas.status.completed',   icon: '✅', bg: 'bg-emerald-100 dark:bg-emerald-900/30', text: 'text-emerald-700 dark:text-emerald-300', progress: 100 },
};

const TIME_RANGES = [
  { labelKey: 'projectIdeas.timeRange.all', value: '' },
  { labelKey: 'projectIdeas.timeRange.lt10', value: '0-10' },
  { labelKey: 'projectIdeas.timeRange.10to30', value: '10-30' },
  { labelKey: 'projectIdeas.timeRange.30to50', value: '30-50' },
  { labelKey: 'projectIdeas.timeRange.gt50', value: '50-999' },
];

const ROLES = [
  { value: 'Backend Developer', labelKey: 'projectIdeas.roles.backend' },
  { value: 'Frontend Developer', labelKey: 'projectIdeas.roles.frontend' },
  { value: 'Full Stack Developer', labelKey: 'projectIdeas.roles.fullstack' },
  { value: 'Data Scientist', labelKey: 'projectIdeas.roles.datascientist' },
  { value: 'DevOps Engineer', labelKey: 'projectIdeas.roles.devops' },
  { value: 'Mobile Developer', labelKey: 'projectIdeas.roles.mobile' },
  { value: 'UI/UX Designer', labelKey: 'projectIdeas.roles.uiux' },
  { value: 'QA Engineer', labelKey: 'projectIdeas.roles.qa' },
];

/* ── Helpers ───────────────────────────────────────────────────── */

function timeAgo(dateStr, t) {
  if (!dateStr) return '';
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return t('projectIdeas.time.minutesAgo', { count: mins });
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return t('projectIdeas.time.hoursAgo', { count: hrs });
  const days = Math.floor(hrs / 24);
  if (days < 30) return t('projectIdeas.time.daysAgo', { count: days });
  return t('projectIdeas.time.monthsAgo', { count: Math.floor(days / 30) });
}

function DifficultyBadge({ level }) {
  const { t } = useTranslation();
  const c = DIFFICULTY_COLORS[level] || DIFFICULTY_COLORS.beginner;
  const label = t(`projectIdeas.difficulty.${level}`);
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold ${c.bg} ${c.text}`}>
      {label}
    </span>
  );
}

/* ── Browse Project Card ──────────────────────────────────────── */

function ProjectCard({ project, userProjectIds, onViewDetails, onAddProject }) {
  const { t } = useTranslation();
  const isAdded = userProjectIds.has(project.project_id);
  const coreSkills = project.core_skills || [];
  const secondarySkills = project.secondary_skills || [];
  const allSkills = [...coreSkills, ...secondarySkills];

  return (
    <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 p-5 hover:shadow-lg hover:border-gray-200 dark:hover:border-gray-700 transition-all group flex flex-col">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <h3 className="text-base font-bold text-gray-900 dark:text-gray-100 line-clamp-2 leading-snug">
          {project.title}
        </h3>
        <DifficultyBadge level={project.difficulty_level} />
      </div>

      {/* Description */}
      <p className="text-sm text-gray-500 dark:text-gray-400 line-clamp-3 mb-3 flex-grow">
        {project.description}
      </p>

      {/* Meta */}
      <div className="flex flex-wrap items-center gap-2 mb-3">
        <span className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 px-2 py-1 rounded-lg">
          <Target className="w-3 h-3" />{project.target_role}
        </span>
        <span className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 px-2 py-1 rounded-lg">
          <Clock className="w-3 h-3" />{project.estimated_hours}h
        </span>
      </div>

      {/* Skills */}
      {allSkills.length > 0 && (
        <div className="mb-4">
          <div className="flex flex-wrap gap-1.5">
            {coreSkills.slice(0, 3).map((s) => (
              <span key={s} className="text-[11px] px-2 py-0.5 rounded-full bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300 font-medium border border-primary-200 dark:border-primary-800">
                {s}
              </span>
            ))}
            {secondarySkills.slice(0, 2).map((s) => (
              <span key={s} className="text-[11px] px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 font-medium">
                {s}
              </span>
            ))}
            {allSkills.length > 5 && (
              <span className="text-[11px] px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-400 dark:text-gray-500">
                +{allSkills.length - 5} {t('projectIdeas.more')}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2 mt-auto pt-2">
        <button
          onClick={() => onViewDetails(project)}
          className="flex-1 h-9 rounded-xl border border-gray-200 dark:border-gray-700 text-sm font-semibold text-gray-600 dark:text-gray-300
            bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors cursor-pointer"
        >
          {t('projectIdeas.actions.viewDetails')}
        </button>
        <button
          onClick={() => !isAdded && onAddProject(project.project_id)}
          disabled={isAdded}
          className={`flex-1 h-9 rounded-xl text-sm font-semibold border-none cursor-pointer transition-all ${
            isAdded
              ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 cursor-default'
              : 'bg-purple-600 text-white hover:bg-purple-700 shadow-sm shadow-purple-600/20'
          }`}
        >
          {isAdded ? t('projectIdeas.actions.added') : t('projectIdeas.actions.addToMyProjects')}
        </button>
      </div>
    </div>
  );
}

/* ── Project Detail Modal ─────────────────────────────────────── */

function ProjectDetailModal({ project, userProjectIds, onClose, onAddProject, onStartProject }) {
  const { t } = useTranslation();
  if (!project) return null;
  const isAdded = userProjectIds.has(project.project_id);
  const coreSkills = project.core_skills || [];
  const secondarySkills = project.secondary_skills || [];
  const dc = DIFFICULTY_COLORS[project.difficulty_level] || DIFFICULTY_COLORS.beginner;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-2xl w-full max-w-xl max-h-[85vh] overflow-y-auto z-10">
        {/* Header */}
        <div className="sticky top-0 bg-white dark:bg-gray-900 border-b border-gray-100 dark:border-gray-800 px-6 py-4 flex items-start justify-between gap-4 z-10">
          <div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">{project.title}</h2>
            <div className="flex items-center gap-2">
              <DifficultyBadge level={project.difficulty_level} />
              <span className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 px-2 py-1 rounded-lg">
                <Target className="w-3 h-3" />{project.target_role}
              </span>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 bg-transparent border-none cursor-pointer">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="px-6 py-5 space-y-5">
          {/* Description */}
          <div>
            <h3 className="text-sm font-bold text-gray-900 dark:text-gray-100 mb-2">{t('projectIdeas.modal.overview')}</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed whitespace-pre-line">{project.description}</p>
          </div>

          {/* Skills */}
          {coreSkills.length > 0 && (
            <div>
              <h3 className="text-sm font-bold text-gray-900 dark:text-gray-100 mb-2">{t('projectIdeas.modal.coreSkills')}</h3>
              <div className="flex flex-wrap gap-2">
                {coreSkills.map((s) => (
                  <span key={s} className="text-xs px-3 py-1.5 rounded-full bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300 font-medium border border-primary-200 dark:border-primary-800">
                    {s}
                  </span>
                ))}
              </div>
            </div>
          )}

          {secondarySkills.length > 0 && (
            <div>
              <h3 className="text-sm font-bold text-gray-900 dark:text-gray-100 mb-2">{t('projectIdeas.modal.optionalSkills')}</h3>
              <div className="flex flex-wrap gap-2">
                {secondarySkills.map((s) => (
                  <span key={s} className="text-xs px-3 py-1.5 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 font-medium">
                    {s}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Project details */}
          <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500 dark:text-gray-400">{t('projectIdeas.modal.estimatedTime')}</span>
              <span className="text-sm font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-1">
                <Clock className="w-4 h-4" />{project.estimated_hours} {t('projectIdeas.units.hours')}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500 dark:text-gray-400">{t('projectIdeas.modal.difficulty')}</span>
              <DifficultyBadge level={project.difficulty_level} />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500 dark:text-gray-400">{t('projectIdeas.modal.suggestedFor')}</span>
              <span className="text-sm font-semibold text-gray-900 dark:text-gray-100">{project.target_role}</span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-white dark:bg-gray-900 border-t border-gray-100 dark:border-gray-800 px-6 py-4 flex gap-3">
          <button onClick={onClose} className="flex-1 h-11 rounded-xl border border-gray-200 dark:border-gray-700 text-sm font-semibold text-gray-600 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors cursor-pointer">
            {t('projectIdeas.actions.cancel')}
          </button>
          {isAdded ? (
            <button
              onClick={() => { onStartProject(project.project_id); onClose(); }}
              className="flex-1 h-11 rounded-xl bg-primary-600 text-white text-sm font-semibold border-none cursor-pointer hover:bg-primary-700 transition-colors shadow-sm shadow-primary-600/20"
            >
              {t('projectIdeas.actions.startProject')}
            </button>
          ) : (
            <button
              onClick={() => { onAddProject(project.project_id); onClose(); }}
              className="flex-1 h-11 rounded-xl bg-purple-600 text-white text-sm font-semibold border-none cursor-pointer hover:bg-purple-700 transition-colors shadow-sm shadow-purple-600/20"
            >
              {t('projectIdeas.actions.addToMyProjects')}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

/* ── Edit User Project Modal ──────────────────────────────────── */

function EditProjectModal({ userProject, onClose, onSave, onDelete }) {
  const { t } = useTranslation();
  const [status, setStatus] = useState(userProject?.status || 'planned');
  const [githubUrl, setGithubUrl] = useState(userProject?.github_url || '');
  const [liveDemoUrl, setLiveDemoUrl] = useState(userProject?.live_demo_url || '');
  const [notes, setNotes] = useState(userProject?.notes || '');
  const [saving, setSaving] = useState(false);

  if (!userProject) return null;

  const handleSave = async () => {
    setSaving(true);
    await onSave(userProject.project_id, { status, github_url: githubUrl, live_demo_url: liveDemoUrl, notes });
    setSaving(false);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-2xl w-full max-w-md z-10">
        <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between">
          <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">{t('projectIdeas.edit.title')}</h2>
          <button onClick={onClose} className="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 bg-transparent border-none cursor-pointer">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="px-6 py-5 space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1.5">{t('projectIdeas.edit.status')}</label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="w-full h-10 px-3 rounded-xl border border-gray-200 dark:border-gray-700 text-sm text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-800 outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
            >
              <option value="planned">{t('projectIdeas.status.planned')}</option>
              <option value="in_progress">{t('projectIdeas.status.in_progress')}</option>
              <option value="completed">{t('projectIdeas.status.completed')}</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1.5">{t('projectIdeas.edit.github')}</label>
            <input
              type="url"
              value={githubUrl}
              onChange={(e) => setGithubUrl(e.target.value)}
              placeholder="https://github.com/..."
              className="w-full h-10 px-3 rounded-xl border border-gray-200 dark:border-gray-700 text-sm text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-800 outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1.5">{t('projectIdeas.edit.demo')}</label>
            <input
              type="url"
              value={liveDemoUrl}
              onChange={(e) => setLiveDemoUrl(e.target.value)}
              placeholder="https://..."
              className="w-full h-10 px-3 rounded-xl border border-gray-200 dark:border-gray-700 text-sm text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-800 outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1.5">{t('projectIdeas.edit.notes')}</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              placeholder={t('projectIdeas.edit.notesPlaceholder')}
              className="w-full px-3 py-2.5 rounded-xl border border-gray-200 dark:border-gray-700 text-sm text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-800 outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 resize-none"
            />
          </div>
        </div>

        <div className="px-6 py-4 border-t border-gray-100 dark:border-gray-800 flex items-center justify-between">
          <button
            onClick={() => { onDelete(userProject.project_id); onClose(); }}
            className="text-sm text-red-500 hover:text-red-600 font-medium bg-transparent border-none cursor-pointer flex items-center gap-1"
          >
            <Trash2 className="w-3.5 h-3.5" /> {t('projectIdeas.actions.delete')}
          </button>
          <div className="flex gap-2">
            <button onClick={onClose} className="h-10 px-4 rounded-xl border border-gray-200 dark:border-gray-700 text-sm font-semibold text-gray-600 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors cursor-pointer">
              {t('projectIdeas.actions.cancel')}
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="h-10 px-5 rounded-xl bg-primary-600 text-white text-sm font-semibold border-none cursor-pointer hover:bg-primary-700 transition-colors disabled:opacity-60"
            >
              {saving ? t('projectIdeas.actions.saving') : t('projectIdeas.actions.saveChanges')}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ── User Project Card (My Projects Tab) ──────────────────────── */

function UserProjectCard({ up, onEdit, onStart, onComplete }) {
  const { t } = useTranslation();
  const cfg = STATUS_CONFIG[up.status] || STATUS_CONFIG.planned;
  const coreSkills = up.core_skills || [];

  return (
    <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 p-5 hover:shadow-md transition-all">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="min-w-0">
          <h3 className="text-base font-bold text-gray-900 dark:text-gray-100 truncate">{up.title}</h3>
          <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">{up.target_role}</p>
        </div>
        <DifficultyBadge level={up.difficulty_level} />
      </div>

      {/* Status badge */}
      <div className="flex items-center gap-2 mb-3">
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold ${cfg.bg} ${cfg.text}`}>
          {cfg.icon} {t(cfg.labelKey)}
        </span>
        <span className="text-xs text-gray-400 dark:text-gray-500 flex items-center gap-1">
          <Clock className="w-3 h-3" />{up.estimated_hours}h
        </span>
      </div>

      {/* Progress bar */}
      <div className="w-full h-2 bg-gray-100 dark:bg-gray-800 rounded-full mb-3">
        <div
          className={`h-2 rounded-full transition-all duration-500 ${
            up.status === 'completed' ? 'bg-emerald-500' : up.status === 'in_progress' ? 'bg-blue-500' : 'bg-gray-300 dark:bg-gray-600'
          }`}
          style={{ width: `${cfg.progress}%` }}
        />
      </div>

      {/* Date info */}
      <div className="text-xs text-gray-400 dark:text-gray-500 mb-3">
        {up.status === 'planned' && up.started_at === null && t('projectIdeas.my.addedToProjects')}
        {up.status === 'in_progress' && up.started_at && `${t('projectIdeas.my.started')} ${timeAgo(up.started_at, t)}`}
        {up.status === 'completed' && up.completed_at && `${t('projectIdeas.my.completed')} ${timeAgo(up.completed_at, t)}`}
      </div>

      {/* Links */}
      {(up.github_url || up.live_demo_url) && (
        <div className="flex gap-2 mb-3">
          {up.github_url && (
            <a href={up.github_url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 no-underline">
              <Github className="w-3.5 h-3.5" /> {t('projectIdeas.edit.github')}
            </a>
          )}
          {up.live_demo_url && (
            <a href={up.live_demo_url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 no-underline">
              <ExternalLink className="w-3.5 h-3.5" /> {t('projectIdeas.edit.demo')}
            </a>
          )}
        </div>
      )}

      {/* Notes preview */}
      {up.notes && (
        <p className="text-xs text-gray-400 dark:text-gray-500 line-clamp-1 mb-3 italic">"{up.notes}"</p>
      )}

      {/* Skills */}
      {coreSkills.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-4">
          {coreSkills.slice(0, 3).map((s) => (
            <span key={s} className="text-[10px] px-2 py-0.5 rounded-full bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300 font-medium">
              {s}
            </span>
          ))}
          {coreSkills.length > 3 && (
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-400 dark:text-gray-500">+{coreSkills.length - 3}</span>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2">
        {up.status === 'planned' && (
          <>
            <button onClick={() => onStart(up.project_id)} className="flex-1 h-9 rounded-xl bg-primary-600 text-white text-sm font-semibold border-none cursor-pointer hover:bg-primary-700 transition-colors flex items-center justify-center gap-1.5">
              <Play className="w-3.5 h-3.5" /> {t('projectIdeas.actions.startProject')}
            </button>
            <button onClick={() => onEdit(up)} className="h-9 px-3 rounded-xl border border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors cursor-pointer">
              <Edit3 className="w-4 h-4" />
            </button>
          </>
        )}
        {up.status === 'in_progress' && (
          <>
            <button onClick={() => onComplete(up.project_id)} className="flex-1 h-9 rounded-xl bg-emerald-600 text-white text-sm font-semibold border-none cursor-pointer hover:bg-emerald-700 transition-colors flex items-center justify-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5" /> {t('projectIdeas.actions.markComplete')}
            </button>
            <button onClick={() => onEdit(up)} className="h-9 px-3 rounded-xl border border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors cursor-pointer">
              <Edit3 className="w-4 h-4" />
            </button>
          </>
        )}
        {up.status === 'completed' && (
          <>
            <button onClick={() => onEdit(up)} className="flex-1 h-9 rounded-xl border border-gray-200 dark:border-gray-700 text-sm font-semibold text-gray-600 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors cursor-pointer flex items-center justify-center gap-1.5">
              <Edit3 className="w-3.5 h-3.5" /> {t('projectIdeas.actions.viewDetails')}
            </button>
          </>
        )}
      </div>
    </div>
  );
}

/* ── Stats Row ────────────────────────────────────────────────── */

function StatsRow({ userProjects }) {
  const { t } = useTranslation();
  const total = userProjects.length;
  const inProgress = userProjects.filter(p => p.status === 'in_progress').length;
  const completed = userProjects.filter(p => p.status === 'completed').length;
  const rate = total > 0 ? Math.round((completed / total) * 100) : 0;

  const stats = [
    { icon: <FolderOpen className="w-5 h-5 text-primary-600" />, bg: 'bg-primary-100 dark:bg-primary-900/30', value: total, label: t('projectIdeas.stats.totalProjects') },
    { icon: <Zap className="w-5 h-5 text-blue-600" />,          bg: 'bg-blue-100 dark:bg-blue-900/30',       value: inProgress, label: t('projectIdeas.status.in_progress') },
    { icon: <CheckCircle2 className="w-5 h-5 text-emerald-600" />, bg: 'bg-emerald-100 dark:bg-emerald-900/30', value: completed, label: t('projectIdeas.status.completed') },
    { icon: <BarChart3 className="w-5 h-5 text-purple-600" />,  bg: 'bg-purple-100 dark:bg-purple-900/30',   value: `${rate}%`, label: t('projectIdeas.stats.completionRate') },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
      {stats.map((s, i) => (
        <div key={i} className="bg-white dark:bg-gray-900 rounded-xl border border-gray-100 dark:border-gray-800 p-4 flex items-center gap-3">
          <div className={`w-10 h-10 ${s.bg} rounded-lg flex items-center justify-center flex-shrink-0`}>
            {s.icon}
          </div>
          <div>
            <p className="text-xl font-bold text-gray-900 dark:text-gray-100">{s.value}</p>
            <p className="text-xs text-gray-400 dark:text-gray-500">{s.label}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

/* ── Filters Bar (Browse Tab) ─────────────────────────────────── */

function FiltersBar({ filters, onChange, onClear, onSearch }) {
  const { t } = useTranslation();
  const hasFilters = filters.role || filters.difficulty || filters.timeRange || filters.search;

  return (
    <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 p-4 mb-6">
      <div className="flex flex-wrap items-end gap-3">
        {/* Search */}
        <div className="flex-1 min-w-[200px]">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 dark:text-gray-500" />
            <input
              type="text"
              value={filters.search}
              onChange={(e) => onChange('search', e.target.value)}
              placeholder={t('projectIdeas.filters.search')}
              className="w-full h-10 pl-9 pr-3 rounded-xl border border-gray-200 dark:border-gray-700 text-sm text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-800 outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 transition-all"
            />
          </div>
        </div>

        {/* Role */}
        <div className="w-[180px]">
          <select
            value={filters.role}
            onChange={(e) => onChange('role', e.target.value)}
            className="w-full h-10 px-3 rounded-xl border border-gray-200 dark:border-gray-700 text-sm text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-800 outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
          >
            <option value="">{t('projectIdeas.filters.allRoles')}</option>
            {ROLES.map((role) => (
              <option key={role.value} value={role.value}>{t(role.labelKey)}</option>
            ))}
          </select>
        </div>

        {/* Difficulty */}
        <div className="w-[150px]">
          <select
            value={filters.difficulty}
            onChange={(e) => onChange('difficulty', e.target.value)}
            className="w-full h-10 px-3 rounded-xl border border-gray-200 dark:border-gray-700 text-sm text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-800 outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
          >
            <option value="">{t('projectIdeas.filters.allDifficulties')}</option>
            <option value="beginner">{t('projectIdeas.difficulty.beginner')}</option>
            <option value="intermediate">{t('projectIdeas.difficulty.intermediate')}</option>
            <option value="advanced">{t('projectIdeas.difficulty.advanced')}</option>
          </select>
        </div>

        {/* Estimated Time */}
        <div className="w-[150px]">
          <select
            value={filters.timeRange}
            onChange={(e) => onChange('timeRange', e.target.value)}
            className="w-full h-10 px-3 rounded-xl border border-gray-200 dark:border-gray-700 text-sm text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-800 outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
          >
            {TIME_RANGES.map((rangeOption) => (
              <option key={rangeOption.value} value={rangeOption.value}>{t(rangeOption.labelKey)}</option>
            ))}
          </select>
        </div>

        {/* Sort */}
        <div className="w-[150px]">
          <select
            value={filters.sort}
            onChange={(e) => onChange('sort', e.target.value)}
            className="w-full h-10 px-3 rounded-xl border border-gray-200 dark:border-gray-700 text-sm text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-800 outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
          >
            <option value="newest">{t('projectIdeas.filters.newestFirst')}</option>
            <option value="difficulty">{t('projectIdeas.filters.difficultySort')}</option>
            <option value="time">{t('projectIdeas.filters.timeSort')}</option>
          </select>
        </div>

        {/* Clear */}
        {hasFilters && (
          <button onClick={onClear} className="h-10 px-3 rounded-xl border border-gray-200 dark:border-gray-700 text-sm text-gray-500 dark:text-gray-400 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors cursor-pointer flex items-center gap-1">
            <X className="w-3.5 h-3.5" /> {t('projectIdeas.filters.clear')}
          </button>
        )}
      </div>

      {/* Quick filter chips */}
      <div className="flex gap-2 mt-3">
        <button
          onClick={() => onChange('quickFilter', filters.quickFilter === 'quick_wins' ? '' : 'quick_wins')}
          className={`px-3 py-1.5 rounded-full text-xs font-medium border cursor-pointer transition-all ${
            filters.quickFilter === 'quick_wins'
              ? 'bg-primary-600 text-white border-primary-600'
              : 'bg-white dark:bg-gray-800 text-gray-500 dark:text-gray-400 border-gray-200 dark:border-gray-700 hover:border-primary-300 dark:hover:border-primary-700'
          }`}
        >
          ⚡ {t('projectIdeas.filters.quickWins')}
        </button>
      </div>
    </div>
  );
}

/* ── Main Page ────────────────────────────────────────────────── */

export default function ProjectIdeasPage() {
  const { t, i18n } = useTranslation();
  const { user, fetchUser } = useAuthStore();
  const [tab, setTab] = useState('browse'); // browse | my
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  // Browse state
  const [browseProjects, setBrowseProjects] = useState([]);
  const [filters, setFilters] = useState({ search: '', role: '', difficulty: '', timeRange: '', sort: 'newest', quickFilter: '' });

  // My Projects state
  const [userProjects, setUserProjects] = useState([]);
  const [statusFilter, setStatusFilter] = useState('all');

  // Modals
  const [detailProject, setDetailProject] = useState(null);
  const [editProject, setEditProject] = useState(null);

  // User project IDs for "Added" state
  const userProjectIds = useMemo(
    () => new Set(userProjects.map(p => p.project_id)),
    [userProjects]
  );

  useEffect(() => {
    fetchUser();
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [browseRes, myRes] = await Promise.all([
        api.get('/projects/all/', { params: { limit: 50 } }).catch(() => ({ data: { projects: [] } })),
        api.get('/projects/my/').catch(() => ({ data: { projects: [] } })),
      ]);
      setBrowseProjects(browseRes.data.projects || []);
      setUserProjects(myRes.data.projects || []);
    } catch {
      // ignore
    }
    setLoading(false);
  };

  const loadBrowseForRole = async (role) => {
    setLoading(true);
    try {
      const { data } = role
        ? await api.get(`/projects/role/${encodeURIComponent(role)}/`, { params: { limit: 50 } })
        : await api.get('/projects/all/', { params: { limit: 50 } });
      setBrowseProjects(data.projects || []);
    } catch {
      // ignore
    }
    setLoading(false);
  };

  // When role filter changes, reload from API
  useEffect(() => {
    if (tab === 'browse') {
      loadBrowseForRole(filters.role);
    }
  }, [filters.role]);

  const generateProjects = async () => {
    setGenerating(true);
    try {
      const payload = {
        target_role: filters.role || 'Full Stack Developer',
        difficulty_level: filters.difficulty || 'beginner',
        language: i18n.language || 'en',
        count: 3,
      };
      const { data } = await api.post('/projects/generate/', payload);
      if (data.success) {
        setBrowseProjects(prev => [...(data.projects || []), ...prev]);
      }
    } catch {
      // ignore
    }
    setGenerating(false);
  };

  const addProject = async (projectId) => {
    try {
      await api.post(`/projects/${projectId}/start/`);
      const { data } = await api.get('/projects/my/');
      setUserProjects(data.projects || []);
    } catch {
      // ignore
    }
  };

  const startProject = async (projectId) => {
    try {
      await api.post(`/projects/${projectId}/start/`);
      const { data } = await api.get('/projects/my/');
      setUserProjects(data.projects || []);
    } catch {
      // ignore
    }
  };

  const completeProject = async (projectId) => {
    try {
      await api.put(`/projects/${projectId}/status/`, { status: 'completed' });
      const { data } = await api.get('/projects/my/');
      setUserProjects(data.projects || []);
    } catch {
      // ignore
    }
  };

  const updateProject = async (projectId, updates) => {
    try {
      await api.put(`/projects/${projectId}/status/`, updates);
      const { data } = await api.get('/projects/my/');
      setUserProjects(data.projects || []);
    } catch {
      // ignore
    }
  };

  const deleteProject = async (projectId) => {
    try {
      await api.put(`/projects/${projectId}/status/`, { status: 'planned' });
      const { data } = await api.get('/projects/my/');
      setUserProjects(data.projects || []);
    } catch {
      // ignore
    }
  };

  const updateFilter = (key, val) => {
    setFilters(f => ({ ...f, [key]: val }));
  };

  const clearFilters = () => {
    setFilters({ search: '', role: '', difficulty: '', timeRange: '', sort: 'newest', quickFilter: '' });
  };

  // Filter + sort browse projects client-side
  const filteredBrowse = useMemo(() => {
    let list = [...browseProjects];

    if (filters.search) {
      const q = filters.search.toLowerCase();
      list = list.filter(p => p.title.toLowerCase().includes(q) || p.description.toLowerCase().includes(q));
    }
    if (filters.difficulty) {
      list = list.filter(p => p.difficulty_level === filters.difficulty);
    }
    if (filters.timeRange) {
      const [min, max] = filters.timeRange.split('-').map(Number);
      list = list.filter(p => p.estimated_hours >= min && p.estimated_hours <= max);
    }
    if (filters.quickFilter === 'quick_wins') {
      list = list.filter(p => p.estimated_hours < 10);
    }

    // Sort
    if (filters.sort === 'difficulty') {
      const order = { beginner: 0, intermediate: 1, advanced: 2 };
      list.sort((a, b) => (order[a.difficulty_level] || 0) - (order[b.difficulty_level] || 0));
    } else if (filters.sort === 'time') {
      list.sort((a, b) => a.estimated_hours - b.estimated_hours);
    }
    // newest = default order from API

    return list;
  }, [browseProjects, filters]);

  // Filter my projects
  const filteredMyProjects = useMemo(() => {
    if (statusFilter === 'all') return userProjects;
    return userProjects.filter(p => p.status === statusFilter);
  }, [userProjects, statusFilter]);

  const statusCounts = useMemo(() => ({
    all: userProjects.length,
    planned: userProjects.filter(p => p.status === 'planned').length,
    in_progress: userProjects.filter(p => p.status === 'in_progress').length,
    completed: userProjects.filter(p => p.status === 'completed').length,
  }), [userProjects]);

  const currentUser = useAuthStore.getState().user || user;

  return (
    <DashboardLayout user={currentUser}>
      {/* Page header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-1">
          <div className="w-10 h-10 bg-gradient-to-br from-amber-100 to-orange-200 dark:from-amber-900/40 dark:to-orange-900/40 rounded-xl flex items-center justify-center">
            <Lightbulb className="w-5 h-5 text-amber-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{t('projectIdeas.title')}</h1>
            <p className="text-sm text-gray-400 dark:text-gray-500">{t('projectIdeas.subtitle')}</p>
          </div>
        </div>
      </div>

      {/* Tab toggle */}
      <div className="flex items-center gap-3 mb-6">
        <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-800 p-1.5 inline-flex gap-1">
          <button
            onClick={() => setTab('browse')}
            className={`px-5 py-2.5 rounded-xl text-sm font-semibold border-none cursor-pointer transition-all ${
              tab === 'browse'
                ? 'bg-primary-600 text-white shadow-sm shadow-primary-600/20'
                : 'bg-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800'
            }`}
          >
            {t('projectIdeas.tabs.browse')}
          </button>
          <button
            onClick={() => setTab('my')}
            className={`px-5 py-2.5 rounded-xl text-sm font-semibold border-none cursor-pointer transition-all flex items-center gap-2 ${
              tab === 'my'
                ? 'bg-primary-600 text-white shadow-sm shadow-primary-600/20'
                : 'bg-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800'
            }`}
          >
            {t('projectIdeas.tabs.my')}
            {userProjects.length > 0 && (
              <span className={`text-xs px-1.5 py-0.5 rounded-full ${
                tab === 'my' ? 'bg-white/20 text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
              }`}>
                {userProjects.length}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* Loading */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-7 h-7 text-primary-500 animate-spin" />
        </div>
      ) : tab === 'browse' ? (
        /* ── Browse Tab ──────────────────────────────────── */
        <>
          <FiltersBar filters={filters} onChange={updateFilter} onClear={clearFilters} />

          {/* Results count + Generate button */}
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {t('projectIdeas.showing', { count: filteredBrowse.length })}
            </p>
            <button
              onClick={generateProjects}
              disabled={generating}
              className="flex items-center gap-2 h-10 px-5 rounded-xl bg-gradient-to-r from-purple-600 to-primary-600 text-white text-sm font-semibold border-none cursor-pointer hover:from-purple-700 hover:to-primary-700 transition-all disabled:opacity-60 shadow-sm"
            >
              {generating ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Sparkles className="w-4 h-4" />
              )}
              {generating ? t('projectIdeas.actions.generating') : t('projectIdeas.actions.generateMore')}
            </button>
          </div>

          {/* Project grid */}
          {filteredBrowse.length === 0 ? (
            <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 p-12 text-center">
              <Search className="w-10 h-10 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">{t('projectIdeas.empty.filteredTitle')}</p>
              <p className="text-xs text-gray-400 dark:text-gray-500 mb-4">{t('projectIdeas.empty.filteredSub')}</p>
              <div className="flex gap-2 justify-center">
                <button onClick={clearFilters} className="px-4 py-2 rounded-lg border border-gray-200 dark:border-gray-700 text-sm text-gray-600 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors cursor-pointer">
                  {t('projectIdeas.filters.clear')}
                </button>
                <button onClick={generateProjects} disabled={generating} className="px-4 py-2 rounded-lg bg-purple-600 text-white text-sm font-semibold border-none cursor-pointer hover:bg-purple-700 transition-colors disabled:opacity-60">
                  {t('projectIdeas.actions.generateProjects')}
                </button>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {filteredBrowse.map((project) => (
                <ProjectCard
                  key={project.project_id}
                  project={project}
                  userProjectIds={userProjectIds}
                  onViewDetails={setDetailProject}
                  onAddProject={addProject}
                />
              ))}
            </div>
          )}
        </>
      ) : (
        /* ── My Projects Tab ─────────────────────────────── */
        <>
          <StatsRow userProjects={userProjects} />

          {/* Status sub-tabs */}
          <div className="flex gap-2 mb-6 overflow-x-auto">
            {(['all', 'planned', 'in_progress', 'completed']).map((s) => {
              const labels = {
                all: t('projectIdeas.status.all'),
                planned: t('projectIdeas.status.planned'),
                in_progress: t('projectIdeas.status.in_progress'),
                completed: t('projectIdeas.status.completed')
              };
              return (
                <button
                  key={s}
                  onClick={() => setStatusFilter(s)}
                  className={`px-4 py-2 rounded-xl text-sm font-medium border cursor-pointer transition-all whitespace-nowrap flex items-center gap-2 ${
                    statusFilter === s
                      ? 'bg-primary-600 text-white border-primary-600'
                      : 'bg-white dark:bg-gray-900 text-gray-500 dark:text-gray-400 border-gray-200 dark:border-gray-700 hover:border-primary-300 dark:hover:border-primary-700'
                  }`}
                >
                  {labels[s]}
                  <span className={`text-xs px-1.5 py-0.5 rounded-full ${
                    statusFilter === s ? 'bg-white/20 text-white' : 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400'
                  }`}>
                    {statusCounts[s]}
                  </span>
                </button>
              );
            })}
          </div>

          {/* My projects grid */}
          {filteredMyProjects.length === 0 ? (
            <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 p-12 text-center">
              <FolderOpen className="w-10 h-10 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">{t('projectIdeas.empty.noProjectsTitle')}</p>
              <p className="text-xs text-gray-400 dark:text-gray-500 mb-4">{t('projectIdeas.empty.noProjectsSub')}</p>
              <button onClick={() => setTab('browse')} className="px-5 py-2.5 rounded-xl bg-primary-600 text-white text-sm font-semibold border-none cursor-pointer hover:bg-primary-700 transition-colors">
                {t('projectIdeas.tabs.browse')}
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {filteredMyProjects.map((up) => (
                <UserProjectCard
                  key={up.user_project_id}
                  up={up}
                  onEdit={setEditProject}
                  onStart={startProject}
                  onComplete={completeProject}
                />
              ))}
            </div>
          )}
        </>
      )}

      {/* Modals */}
      {detailProject && (
        <ProjectDetailModal
          project={detailProject}
          userProjectIds={userProjectIds}
          onClose={() => setDetailProject(null)}
          onAddProject={addProject}
          onStartProject={startProject}
        />
      )}
      {editProject && (
        <EditProjectModal
          userProject={editProject}
          onClose={() => setEditProject(null)}
          onSave={updateProject}
          onDelete={deleteProject}
        />
      )}
    </DashboardLayout>
  );
}
