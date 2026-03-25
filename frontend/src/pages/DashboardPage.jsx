import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Zap, TrendingUp, Target, Briefcase, BarChart3, Code2,
  Clock, Lock, ChevronRight, ArrowRight, Sparkles,
  CheckCircle2, MessageSquare, Loader2,
  AlertCircle,
} from 'lucide-react';
import { formatRelativeTime, getActivityVisual } from '../utils/activityFeed';
import api from '../services/api';
import useAuthStore from '../store/authStore';
import DashboardLayout from '../components/layout/DashboardLayout';

/* ── colour helpers ─────────────────────────────────────────────── */

const PROFICIENCY_COLORS = {
  expert:       { bg: 'bg-emerald-100', text: 'text-emerald-700', border: 'border-l-emerald-500' },
  advanced:     { bg: 'bg-blue-100',    text: 'text-blue-700',    border: 'border-l-blue-500' },
  intermediate: { bg: 'bg-amber-100',   text: 'text-amber-700',   border: 'border-l-amber-500' },
  beginner:     { bg: 'bg-gray-100',    text: 'text-gray-600',    border: 'border-l-gray-400' },
};

const PRIORITY_STYLES = {
  high:   { badge: 'bg-red-100 text-red-700', border: 'border-l-red-500', btn: 'bg-red-600 hover:bg-red-700 text-white' },
  medium: { badge: 'bg-orange-100 text-orange-700', border: 'border-l-orange-500', btn: 'border border-orange-500 text-orange-600 hover:bg-orange-50' },
  low:    { badge: 'bg-blue-100 text-blue-700', border: 'border-l-blue-500', btn: 'border border-blue-500 text-blue-600 hover:bg-blue-50' },
};

/* ── Welcome Banner ─────────────────────────────────────────────── */

function WelcomeBanner({ user, profile, completion }) {
  const firstName = user?.first_name || user?.email?.split('@')[0] || 'User';
  const role = profile?.current_job_position || profile?.desired_role || '';
  const level = profile?.experience_level
    ? profile.experience_level.charAt(0).toUpperCase() + profile.experience_level.slice(1)
    : '';
  const pct = completion?.completion_percentage ?? 0;

  return (
    <div className="bg-gradient-to-r from-primary-600 via-primary-700 to-purple-600 rounded-2xl p-6 sm:p-8 text-white flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold mb-1">
          Welcome back, {firstName}! 👋
        </h1>
        {(role || level) && (
          <span className="inline-flex items-center gap-2 mt-2 px-3 py-1 bg-white/15 backdrop-blur-sm rounded-full text-sm font-medium">
            {role}{role && level && ' • '}{level}
          </span>
        )}
      </div>

      <div className="flex items-center gap-4">
        <div className="relative w-16 h-16">
          <svg viewBox="0 0 36 36" className="w-16 h-16 -rotate-90">
            <circle cx="18" cy="18" r="15.9" fill="none" stroke="rgba(255,255,255,0.2)" strokeWidth="3" />
            <circle
              cx="18" cy="18" r="15.9" fill="none" stroke="white" strokeWidth="3"
              strokeDasharray={`${pct} ${100 - pct}`} strokeLinecap="round"
            />
          </svg>
          <span className="absolute inset-0 flex items-center justify-center text-sm font-bold">{pct}%</span>
        </div>
        <div className="text-sm">
          <p className="font-semibold">Profile Completion</p>
          {pct < 100 && (
            <Link to="/profile-setup" className="inline-flex items-center gap-1 text-white/80 hover:text-white text-xs no-underline mt-0.5">
              Complete your profile <ChevronRight className="w-3 h-3" />
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}

/* ── Quick Stats ────────────────────────────────────────────────── */

function QuickStats({ skills, hasGapAnalysis, primaryRoadmap, gapPendingLearning, recommendations }) {
  const totalSkills = skills?.length || 0;
  const primarySkills = skills?.filter(s => s.is_primary).length || 0;
  const jobMatches = recommendations?.length || 0;
  const skillsToLearn = gapPendingLearning > 0 ? gapPendingLearning : 0;

  const roadmapPct = primaryRoadmap?.completion_percentage != null
    ? Math.round(primaryRoadmap.completion_percentage)
    : null;
  let roadmapSub = 'Run skill gap analysis first';
  if (hasGapAnalysis && primaryRoadmap && primaryRoadmap.stats) {
    const { completed = 0, total_items: totalItems = 0 } = primaryRoadmap.stats;
    roadmapSub = `${completed} of ${totalItems} roadmap steps`;
  } else if (hasGapAnalysis && !primaryRoadmap?.items?.length) {
    roadmapSub = 'Generate your roadmap';
  } else if (hasGapAnalysis && roadmapPct != null) {
    roadmapSub = `${totalSkills} skills on profile`;
  }

  const cards = [
    {
      icon: <BarChart3 className="w-5 h-5 text-primary-600" />,
      iconBg: 'bg-primary-100',
      value: hasGapAnalysis && roadmapPct != null ? `${roadmapPct}%` : '—',
      label: 'Roadmap Progress',
      sub: roadmapSub,
      color: 'text-primary-600',
    },
    {
      icon: <Code2 className="w-5 h-5 text-emerald-600" />,
      iconBg: 'bg-emerald-100',
      value: totalSkills,
      label: 'Total Skills',
      sub: `${primarySkills} primary`,
      color: 'text-emerald-600',
    },
    {
      icon: <Target className="w-5 h-5 text-orange-600" />,
      iconBg: 'bg-orange-100',
      value: hasGapAnalysis ? skillsToLearn : '—',
      label: 'Skills to Learn',
      sub: skillsToLearn > 0 ? 'From your skill gap analysis' : (hasGapAnalysis ? 'No open gaps' : 'Run analysis to see gaps'),
      color: 'text-orange-600',
    },
    {
      icon: <Briefcase className="w-5 h-5 text-purple-600" />,
      iconBg: 'bg-purple-100',
      value: jobMatches,
      label: 'Job Matches',
      sub: 'Based on your profile',
      color: 'text-purple-600',
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((c, i) => (
        <div key={i} className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5 hover:shadow-md transition-shadow">
          <div className={`w-10 h-10 ${c.iconBg} rounded-lg flex items-center justify-center mb-3`}>
            {c.icon}
          </div>
          <p className={`text-2xl font-bold ${c.color}`}>{c.value}</p>
          <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mt-0.5">{c.label}</p>
          <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">{c.sub}</p>
        </div>
      ))}
    </div>
  );
}

/* ── Your Skills ────────────────────────────────────────────────── */

function YourSkills({ skills }) {
  if (!skills || skills.length === 0) {
    return (
      <Section title="Your Skills" actionLabel="Add Skills" actionTo="/manage-skills">
        <div className="text-center py-10 text-gray-400 dark:text-gray-500">
          <Code2 className="w-10 h-10 mx-auto mb-3 opacity-50" />
          <p className="text-sm">No skills added yet.</p>
          <Link to="/manage-skills" className="text-primary-600 text-sm font-medium no-underline hover:underline mt-1 inline-block">
            Add your skills
          </Link>
        </div>
      </Section>
    );
  }

  const order = ['expert', 'advanced', 'intermediate', 'beginner'];
  const sorted = [...skills].sort((a, b) => order.indexOf(a.proficiency_level) - order.indexOf(b.proficiency_level));

  return (
    <Section title="Your Skills" actionLabel="View All" actionTo="/manage-skills">
      <div className="flex flex-wrap gap-2">
        {sorted.map((s) => {
          const colors = PROFICIENCY_COLORS[s.proficiency_level] || PROFICIENCY_COLORS.beginner;
          return (
            <span
              key={s.user_skill_id}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border-l-4 ${colors.bg} ${colors.text} ${colors.border} hover:shadow-sm transition-shadow`}
            >
              {s.skill_name || 'Skill'}
            </span>
          );
        })}
      </div>
      <div className="flex gap-3 mt-3 text-xs text-gray-400 dark:text-gray-500">
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500" /> Expert</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-blue-500" /> Advanced</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-500" /> Intermediate</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-gray-400" /> Beginner</span>
      </div>
    </Section>
  );
}

/* ── Learning Roadmap Preview ───────────────────────────────────── */

function buildRoadmapPreviewRows(items) {
  if (!items?.length) return [];
  const sorted = [...items]
    .filter((it) => it.status !== 'skipped')
    .sort((a, b) => (a.sequence_order ?? 0) - (b.sequence_order ?? 0));
  const preview = sorted.slice(0, 4);

  const inProgressIdx = sorted.findIndex((it) => it.status === 'in_progress');
  let nextPendingGlobal = sorted.findIndex((it) => it.status === 'pending');
  if (inProgressIdx >= 0) {
    const after = sorted.findIndex((it, idx) => it.status === 'pending' && idx > inProgressIdx);
    if (after >= 0) nextPendingGlobal = after;
  }

  return preview.map((it, idx) => {
    const prev = idx > 0 ? preview[idx - 1] : null;
    const unlocksAfter = prev?.skill_name ?? null;

    if (it.status === 'completed') {
      return {
        key: `done-${it.item_id}`,
        displayStatus: 'completed',
        skill: it.skill_name,
        estHours: it.estimated_duration_hours ?? 0,
        priority: it.priority,
      };
    }
    if (it.status === 'in_progress') {
      return {
        key: `learn-${it.item_id}`,
        displayStatus: 'learning',
        skill: it.skill_name,
        estHours: it.estimated_duration_hours ?? 0,
        priority: it.priority,
        progress: 45,
      };
    }
    const globalIdx = sorted.indexOf(it);
    const isNext = it.status === 'pending' && globalIdx === nextPendingGlobal;
    return {
      key: `pend-${it.item_id}`,
      displayStatus: isNext ? 'next' : 'pending',
      skill: it.skill_name,
      estHours: it.estimated_duration_hours ?? 0,
      priority: it.priority,
      unlocksAfter: isNext ? unlocksAfter : null,
    };
  });
}

function LearningRoadmap({ hasGapAnalysis, primaryRoadmap, topGapSkillNames }) {
  if (!hasGapAnalysis) {
    return (
      <Section title="Your Learning Roadmap">
        <div className="text-center py-10 text-gray-400 dark:text-gray-500">
          <Target className="w-10 h-10 mx-auto mb-3 opacity-50" />
          <p className="text-sm mb-2 max-w-md mx-auto">
            Run a skill gap analysis to compare your profile with real market demand and unlock a personalized learning path.
          </p>
          <Link
            to="/skills-gap"
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium no-underline hover:bg-primary-700 transition-colors"
          >
            Get your roadmap <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </Section>
    );
  }

  const roadmapItems = primaryRoadmap?.items ?? [];
  if (!roadmapItems.length) {
    return (
      <Section title="Your Learning Roadmap" actionLabel="View gaps" actionTo="/skills-gap">
        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
          <p className="text-sm mb-4 max-w-lg mx-auto">
            Your skill gaps are saved. Generate a step-by-step roadmap to turn them into an ordered learning plan.
          </p>
          {topGapSkillNames?.length > 0 && (
            <div className="flex flex-wrap justify-center gap-2 mb-5">
              {topGapSkillNames.slice(0, 6).map((name) => (
                <span
                  key={name}
                  className="text-xs font-medium px-3 py-1 rounded-full bg-primary-50 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300"
                >
                  {name}
                </span>
              ))}
            </div>
          )}
          <Link
            to="/roadmap"
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium no-underline hover:bg-primary-700 transition-colors"
          >
            Build learning roadmap <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </Section>
    );
  }

  const items = buildRoadmapPreviewRows(roadmapItems);

  const statusConfig = {
    completed: { dot: 'bg-emerald-500', badge: 'bg-emerald-100 text-emerald-700', label: 'DONE' },
    learning: { dot: 'bg-emerald-500', badge: 'bg-emerald-100 text-emerald-700', label: 'LEARNING' },
    next: { dot: 'bg-orange-400', badge: 'bg-orange-100 text-orange-700', label: 'NEXT' },
    pending: { dot: 'bg-gray-300', badge: 'bg-gray-100 text-gray-500', label: 'PENDING' },
  };

  return (
    <Section title="Your Learning Roadmap" actionLabel="View full roadmap" actionTo="/roadmap">
      <div className="relative">
        <div className="absolute left-[11px] top-4 bottom-4 w-0.5 bg-gray-200 dark:bg-gray-700" />
        <div className="space-y-6">
          {items.map((item) => {
            const cfg = statusConfig[item.displayStatus];
            const pri = item.priority === 'high' ? 'HIGH' : item.priority === 'medium' ? 'MED' : null;
            return (
              <div key={item.key} className="relative flex gap-4">
                <div className={`relative z-10 w-6 h-6 rounded-full ${cfg.dot} border-4 border-white dark:border-gray-900 shadow-sm flex-shrink-0 mt-1`} />
                <div
                  className={`flex-1 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5 ${
                    item.displayStatus === 'pending' ? 'opacity-60' : ''
                  }`}
                >
                  <div className="flex items-center gap-2 mb-2 flex-wrap">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${cfg.badge}`}>{cfg.label}</span>
                    <span className="text-base font-bold text-gray-900 dark:text-gray-100">{item.skill}</span>
                    {pri && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-100 text-red-700">{pri}</span>
                    )}
                  </div>
                  {item.displayStatus === 'learning' && (
                    <>
                      <div className="w-full h-2 bg-gray-100 dark:bg-gray-800 rounded-full mb-2">
                        <div className="h-2 bg-emerald-500 rounded-full transition-all" style={{ width: `${item.progress}%` }} />
                      </div>
                      <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400 mb-3">
                        {item.estHours > 0 && (
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            Est. {item.estHours} h
                          </span>
                        )}
                      </div>
                      <Link
                        to="/roadmap"
                        className="block w-full py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors text-center no-underline"
                      >
                        Continue learning
                      </Link>
                    </>
                  )}
                  {item.displayStatus === 'next' && (
                    <>
                      <p className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-gray-500 dark:text-gray-400 mb-3">
                        {item.unlocksAfter && (
                          <span className="flex items-center gap-1">
                            <Lock className="w-3 h-3" />
                            After {item.unlocksAfter}
                          </span>
                        )}
                        {item.estHours > 0 && (
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            Est. {item.estHours} h
                          </span>
                        )}
                      </p>
                      <Link
                        to="/roadmap"
                        className="block w-full py-2 border border-gray-300 dark:border-gray-700 text-gray-600 dark:text-gray-300 rounded-lg text-sm font-medium hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors bg-white dark:bg-gray-900 text-center no-underline"
                      >
                        Open roadmap
                      </Link>
                    </>
                  )}
                  {item.displayStatus === 'pending' && (
                    <p className="flex items-center gap-1 text-xs text-gray-400 dark:text-gray-500">
                      {item.estHours > 0 && (
                        <>
                          <Clock className="w-3 h-3" />
                          Est. {item.estHours} h
                        </>
                      )}
                    </p>
                  )}
                  {item.displayStatus === 'completed' && (
                    <p className="text-xs text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      Completed
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </Section>
  );
}

/* ── Skills Gap Analysis (real data only) ───────────────────────── */

function SkillsGapAnalysis({ profile, recommendations, gaps }) {
  if (!gaps?.length) return null;

  const desiredRole = profile?.desired_role || profile?.current_job_position || recommendations?.[0]?.role_name || 'your target role';
  const openGaps = gaps.filter((g) => g.status === 'pending' || g.status === 'learning');
  const preview = (openGaps.length > 0 ? openGaps : gaps).slice(0, 4);

  return (
    <Section
      title={`Skills to close for ${desiredRole}`}
      subtitle="From your latest skill gap analysis"
    >
      <div className="space-y-4">
        {preview.map((gap) => {
          const s = PRIORITY_STYLES[gap.priority] || PRIORITY_STYLES.medium;
          const importanceLabel = gap.importance === 'core' ? 'Core' : 'Secondary';
          const jobLine = gap.job_count > 0 ? `${gap.job_count} postings (30d trend)` : 'Market demand tracked';
          const reason = `${importanceLabel} gap — ${jobLine}.`;

          return (
            <div
              key={gap.gap_id}
              className={`bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 border-l-4 ${s.border} p-5`}
            >
              <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase ${s.badge} mb-2`}>
                {gap.priority} priority · {importanceLabel}
              </span>
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-1">{gap.skill_name}</h3>
              <p className="flex items-start gap-1.5 text-sm text-gray-500 dark:text-gray-400 mb-3">
                <Sparkles className="w-4 h-4 text-purple-500 flex-shrink-0 mt-0.5" />
                {reason}
              </p>
              <div className="flex flex-wrap items-center gap-4 text-xs text-gray-500 dark:text-gray-400 mb-4">
                <span className="flex items-center gap-1">
                  <Zap className="w-3 h-3" />
                  Demand score {typeof gap.demand_score === 'number' ? Math.round(gap.demand_score) : '—'}
                </span>
                {gap.growth_rate ? (
                  <span className="flex items-center gap-1">
                    <TrendingUp className="w-3 h-3" />
                    Growth {gap.growth_rate}%
                  </span>
                ) : null}
              </div>
              <Link
                to="/roadmap"
                className={`block w-full py-2.5 rounded-lg text-sm font-semibold transition-colors text-center no-underline ${s.btn}`}
              >
                View roadmap & resources
              </Link>
            </div>
          );
        })}
      </div>
      <Link to="/skills-gap" className="inline-flex items-center gap-1 text-primary-600 text-sm font-medium no-underline hover:underline mt-4">
        View all skill gaps <ArrowRight className="w-4 h-4" />
      </Link>
    </Section>
  );
}

/* ── Recent Activity ────────────────────────────────────────────── */

function RecentActivity({ activities }) {
  if (!activities?.length) {
    return (
      <Section title="Your recent activity" actionLabel="View all" actionTo="/activity">
        <div className="text-center py-8 text-gray-400 dark:text-gray-500 text-sm">
          <p>No activity recorded yet.</p>
          <p className="mt-1 text-xs">Register, set up your profile, or run skill gap analysis to see your timeline here.</p>
        </div>
      </Section>
    );
  }

  return (
    <Section title="Your recent activity" actionLabel="View all" actionTo="/activity">
      <div className="space-y-3">
        {activities.map((a) => {
          const v = getActivityVisual(a.activity_type);
          const Icon = v.Icon;
          const row = (
            <div className="flex items-center gap-3">
              <div className={`w-8 h-8 ${v.bg} rounded-full flex items-center justify-center flex-shrink-0`}>
                <Icon className={`w-4 h-4 ${v.iconClass}`} />
              </div>
              <p className="text-sm text-gray-700 dark:text-gray-300 flex-1 min-w-0">{a.description}</p>
              <span className="text-xs text-gray-400 dark:text-gray-500 whitespace-nowrap">
                {formatRelativeTime(a.created_at)}
              </span>
            </div>
          );
          return (
            <div key={a.activity_id}>
              {a.link_path ? (
                <Link to={a.link_path} className="block no-underline hover:opacity-90">
                  {row}
                </Link>
              ) : (
                row
              )}
            </div>
          );
        })}
      </div>
    </Section>
  );
}

/* ── Recommended Jobs ───────────────────────────────────────────── */

function RecommendedJobs() {
  const jobs = [
    { title: 'Senior Backend Developer', company: 'Tech Startup Tashkent', salary: '12-15M UZS', match: 88, total: 11, have: 9, missing: ['Kubernetes', 'AWS'] },
    { title: 'Full-Stack Developer', company: 'IT Park Uzbekistan', salary: '10-13M UZS', match: 82, total: 10, have: 8, missing: ['GraphQL', 'TypeScript'] },
    { title: 'DevOps Engineer', company: 'Digital Solutions', salary: '14-18M UZS', match: 75, total: 12, have: 9, missing: ['Terraform', 'Ansible', 'Prometheus'] },
  ];

  const matchColor = (m) => m >= 80 ? 'text-emerald-600' : m >= 60 ? 'text-amber-600' : 'text-gray-500';
  const matchTrack = (m) => m >= 80 ? 'stroke-emerald-500' : m >= 60 ? 'stroke-amber-500' : 'stroke-gray-400';

  return (
    <Section title={`Jobs Matching Your Profile (${jobs.length})`} actionLabel="View All Jobs" actionTo="/jobs">
      <div className="space-y-3">
        {jobs.map((j, i) => (
          <div key={i} className="rounded-xl border border-gray-200 dark:border-gray-800 p-4 hover:shadow-md transition-shadow flex items-start gap-3">
            {/* Left: info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <div className="w-8 h-8 bg-gray-100 dark:bg-gray-800 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Briefcase className="w-4 h-4 text-gray-400 dark:text-gray-500" />
                </div>
                <div className="min-w-0">
                  <h3 className="text-sm font-bold text-gray-900 dark:text-gray-100 truncate">{j.title}</h3>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{j.company}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400 mt-2">
                <span className="flex items-center gap-1"><TrendingUp className="w-3 h-3" />{j.salary}</span>
                <span>{j.have}/{j.total} skills</span>
              </div>
              {j.missing.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {j.missing.slice(0, 2).map((m) => (
                    <span key={m} className="text-[10px] bg-red-50 text-red-600 px-1.5 py-0.5 rounded font-medium">Missing: {m}</span>
                  ))}
                  {j.missing.length > 2 && (
                    <span className="text-[10px] text-gray-400 dark:text-gray-500">+{j.missing.length - 2} more</span>
                  )}
                </div>
              )}
            </div>

            {/* Right: match ring (small) */}
            <div className="relative w-10 h-10 flex-shrink-0">
              <svg viewBox="0 0 36 36" className="w-10 h-10 -rotate-90">
                <circle cx="18" cy="18" r="15.9" fill="none" stroke="#e5e7eb" strokeWidth="3.5" />
                <circle cx="18" cy="18" r="15.9" fill="none" className={matchTrack(j.match)} strokeWidth="3.5" strokeDasharray={`${j.match} ${100 - j.match}`} strokeLinecap="round" />
              </svg>
              <span className={`absolute inset-0 flex items-center justify-center text-[10px] font-bold ${matchColor(j.match)}`}>{j.match}%</span>
            </div>
          </div>
        ))}
      </div>
    </Section>
  );
}

/* ── Bottom CTA ─────────────────────────────────────────────────── */

function BottomCTA() {
  return (
    <div className="bg-gradient-to-r from-primary-50 via-purple-50 to-primary-50 dark:from-primary-900/20 dark:via-purple-900/20 dark:to-primary-900/20 rounded-2xl p-8 text-center">
      <Sparkles className="w-8 h-8 text-purple-500 mx-auto mb-3" />
      <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">Ready to accelerate your learning?</h2>
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-5 max-w-md mx-auto">
        Get personalized recommendations from our AI chatbot
      </p>
      <Link to="/chat" className="inline-flex items-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-xl text-sm font-semibold hover:bg-primary-700 transition-colors border-none cursor-pointer shadow-lg shadow-primary-600/20 no-underline">
        <MessageSquare className="w-4 h-4" />
        Chat Now
      </Link>
    </div>
  );
}

/* ── Shared Section Wrapper ─────────────────────────────────────── */

function Section({ title, subtitle, actionLabel, actionTo, children }) {
  return (
    <section className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-6">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">{title}</h2>
          {subtitle && <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">{subtitle}</p>}
        </div>
        {actionLabel && actionTo && (
          <Link to={actionTo} className="text-sm text-primary-600 font-medium no-underline hover:underline">
            {actionLabel}
          </Link>
        )}
      </div>
      {children}
    </section>
  );
}

/* ── Main Dashboard ─────────────────────────────────────────────── */

export default function DashboardPage() {
  const navigate = useNavigate();
  const { user, fetchUser } = useAuthStore();
  const [profile, setProfile] = useState(null);
  const [skills, setSkills] = useState([]);
  const [completion, setCompletion] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [skillGaps, setSkillGaps] = useState([]);
  const [gapByStatus, setGapByStatus] = useState({ pending: 0, learning: 0, completed: 0 });
  const [primaryRoadmap, setPrimaryRoadmap] = useState(null);
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const staff = user?.is_staff || user?.is_superuser;
    if (user?.user_type === 'recruiter' && !staff) {
      navigate('/recruiter/dashboard', { replace: true });
    }
  }, [user, navigate]);

  useEffect(() => {
    const load = async () => {
      try {
        if (!user) await fetchUser();

        const [summaryRes, statusRes, gapsRes, roadmapsRes, activityRes] = await Promise.all([
          api.get('/users/profile/summary/'),
          api.get('/career/status/').catch(() => ({ data: {} })),
          api.get('/skills/gaps/').catch(() => ({ data: { gaps: [], by_status: {} } })),
          api.get('/roadmaps/').catch(() => ({ data: { roadmaps: [] } })),
          api.get('/users/profile/activity/', { params: { page: 1, page_size: 6 } }).catch(() => ({ data: { results: [] } })),
        ]);

        const summary = summaryRes.data;
        setProfile(summary.profile || summary);

        const skillsList = (summary.skills?.list || []).map((s) => ({
          user_skill_id: s.user_skill_id,
          skill_name: s.name_en,
          category: s.category,
          proficiency_level: s.proficiency,
          years_of_experience: s.years,
          is_primary: s.is_primary,
          source: s.source,
        }));
        setSkills(skillsList);

        setCompletion({
          profile_completed: summary.user?.profile_completed ?? summary.completion?.profile_completed,
          completion_percentage: summary.completion?.completion_percentage ?? (summary.user?.profile_completed ? 100 : 50),
        });
        const gData = gapsRes.data || {};
        setSkillGaps(gData.gaps || []);
        setGapByStatus({
          pending: gData.by_status?.pending ?? 0,
          learning: gData.by_status?.learning ?? 0,
          completed: gData.by_status?.completed ?? 0,
        });

        const roadmaps = roadmapsRes.data?.roadmaps || [];
        setPrimaryRoadmap(roadmaps[0] || null);

        setActivities(activityRes.data?.results || []);

        if (statusRes.data?.has_recommendations) {
          try {
            const recRes = await api.get('/career/recommendations/');
            setRecommendations(recRes.data.recommendations || []);
          } catch {
            // ignore
          }
        }
      } catch (err) {
        if (err.response?.status === 401) {
          window.location.href = '/login?redirect=/dashboard';
          return;
        }
        setError('Failed to load dashboard data.');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const hasGapAnalysis = skillGaps.length > 0;
  const gapPendingLearning = (gapByStatus.pending || 0) + (gapByStatus.learning || 0);
  const topGapSkillNames = skillGaps.map((g) => g.skill_name).filter(Boolean);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-primary-600 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-10 h-10 text-red-400 mx-auto mb-3" />
          <p className="text-gray-600 dark:text-gray-300">{error}</p>
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
        <WelcomeBanner user={user} profile={profile} completion={completion} />
        <QuickStats
          skills={skills}
          hasGapAnalysis={hasGapAnalysis}
          primaryRoadmap={primaryRoadmap}
          gapPendingLearning={gapPendingLearning}
          recommendations={recommendations}
        />

        <div className="grid lg:grid-cols-5 gap-6">
          <div className="lg:col-span-3 space-y-6">
            <YourSkills skills={skills} />
            <LearningRoadmap
              hasGapAnalysis={hasGapAnalysis}
              primaryRoadmap={primaryRoadmap}
              topGapSkillNames={topGapSkillNames}
            />
            <SkillsGapAnalysis profile={profile} recommendations={recommendations} gaps={skillGaps} />
          </div>
          <div className="lg:col-span-2 space-y-6">
            <RecentActivity activities={activities} />
            <RecommendedJobs />
          </div>
        </div>

        <BottomCTA />
      </div>
    </DashboardLayout>
  );
}
