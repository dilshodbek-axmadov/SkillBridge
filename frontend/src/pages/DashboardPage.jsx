import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Zap, TrendingUp, Target, Briefcase, BarChart3, Code2,
  Clock, Book, Lock, ChevronRight, ArrowRight, Sparkles,
  CheckCircle2, Star, Trophy, MessageSquare, Loader2,
  AlertCircle,
} from 'lucide-react';
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

function QuickStats({ skills, careerStatus, recommendations }) {
  const totalSkills = skills?.length || 0;
  const primarySkills = skills?.filter(s => s.is_primary).length || 0;
  const jobMatches = recommendations?.length || 0;
  const skillsToLearn = Math.max(0, 10 - totalSkills);

  const cards = [
    {
      icon: <BarChart3 className="w-5 h-5 text-primary-600" />,
      iconBg: 'bg-primary-100',
      value: careerStatus?.completed ? '65%' : '—',
      label: 'Roadmap Progress',
      sub: careerStatus?.completed ? `${totalSkills} skills learned` : 'Take assessment first',
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
      value: skillsToLearn,
      label: 'Skills to Learn',
      sub: skillsToLearn > 0 ? 'Based on your profile' : 'Looking great!',
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
          <p className="text-sm font-medium text-gray-700 mt-0.5">{c.label}</p>
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

function LearningRoadmap({ careerStatus }) {
  if (!careerStatus?.completed) {
    return (
      <Section title="Your Learning Roadmap">
        <div className="text-center py-10 text-gray-400 dark:text-gray-500">
          <Target className="w-10 h-10 mx-auto mb-3 opacity-50" />
          <p className="text-sm mb-2">Complete the career assessment to get your personalized roadmap.</p>
          <Link
            to="/assessment"
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium no-underline hover:bg-primary-700 transition-colors"
          >
            Take Assessment <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </Section>
    );
  }

  const items = [
    { status: 'learning', skill: 'Docker', progress: 75, timeLeft: '12 hours left', tutorials: 3 },
    { status: 'next', skill: 'Kubernetes', unlocksAfter: 'Docker', estHours: 20 },
    { status: 'pending', skill: 'AWS', estHours: 30, priority: 'HIGH' },
  ];

  const statusConfig = {
    learning: { dot: 'bg-emerald-500', badge: 'bg-emerald-100 text-emerald-700', label: 'LEARNING' },
    next:     { dot: 'bg-orange-400',  badge: 'bg-orange-100 text-orange-700',   label: 'NEXT' },
    pending:  { dot: 'bg-gray-300',    badge: 'bg-gray-100 text-gray-500',       label: 'PENDING' },
  };

  return (
    <Section title="Your Learning Roadmap" actionLabel="View Full Roadmap" actionTo="/roadmap">
      <div className="relative">
        <div className="absolute left-[11px] top-4 bottom-4 w-0.5 bg-gray-200" />
        <div className="space-y-6">
          {items.map((item, i) => {
            const cfg = statusConfig[item.status];
            return (
              <div key={i} className="relative flex gap-4">
                <div className={`relative z-10 w-6 h-6 rounded-full ${cfg.dot} border-4 border-white shadow-sm flex-shrink-0 mt-1`} />
                <div className={`flex-1 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5 ${item.status === 'pending' ? 'opacity-60' : ''}`}>
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${cfg.badge}`}>{cfg.label}</span>
                    <span className="text-base font-bold text-gray-900 dark:text-gray-100">{item.skill}</span>
                    {item.priority && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-100 text-red-700">{item.priority}</span>
                    )}
                  </div>
                  {item.status === 'learning' && (
                    <>
                      <div className="w-full h-2 bg-gray-100 dark:bg-gray-800 rounded-full mb-2">
                        <div className="h-2 bg-emerald-500 rounded-full" style={{ width: `${item.progress}%` }} />
                      </div>
                      <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400 mb-3">
                        <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{item.timeLeft}</span>
                        <span className="flex items-center gap-1"><Book className="w-3 h-3" />{item.tutorials} tutorials completed</span>
                      </div>
                      <button className="w-full py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors border-none cursor-pointer">
                        Continue Learning
                      </button>
                    </>
                  )}
                  {item.status === 'next' && (
                    <>
                      <p className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400 mb-3">
                        <Lock className="w-3 h-3" /> Unlocks after {item.unlocksAfter}
                        <span className="ml-3 flex items-center gap-1"><Clock className="w-3 h-3" /> Est. {item.estHours} hours</span>
                      </p>
                      <button className="w-full py-2 border border-gray-300 text-gray-600 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors bg-white cursor-pointer">
                        Preview
                      </button>
                    </>
                  )}
                  {item.status === 'pending' && (
                    <p className="flex items-center gap-1 text-xs text-gray-400 dark:text-gray-500">
                      <Clock className="w-3 h-3" /> Est. {item.estHours} hours
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

/* ── Skills Gap Analysis ────────────────────────────────────────── */

function SkillsGapAnalysis({ profile, recommendations }) {
  const desiredRole = profile?.desired_role || recommendations?.[0]?.role_name || 'Senior Backend Developer';

  const gaps = [
    { skill: 'Kubernetes', priority: 'high', reason: 'Essential for senior backend roles — appears in 72% of job postings', jobs: 63, salaryBoost: '+2M UZS avg salary boost', actionLabel: 'Start Learning' },
    { skill: 'GraphQL', priority: 'medium', reason: 'Modern API technology gaining rapid adoption in Uzbek tech companies', jobs: 34, salaryBoost: '', actionLabel: 'Add to Roadmap' },
  ];

  return (
    <Section title={`Skills You Need for ${desiredRole}`} subtitle="Based on 87 job postings analysis">
      <div className="space-y-4">
        {gaps.map((gap, i) => {
          const s = PRIORITY_STYLES[gap.priority];
          return (
            <div key={i} className={`bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 border-l-4 ${s.border} p-5`}>
              <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase ${s.badge} mb-2`}>
                {gap.priority} PRIORITY
              </span>
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-1">{gap.skill}</h3>
              <p className="flex items-start gap-1.5 text-sm text-gray-500 dark:text-gray-400 mb-3">
                <Sparkles className="w-4 h-4 text-purple-500 flex-shrink-0 mt-0.5" />
                {gap.reason}
              </p>
              <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400 mb-4">
                <span className="flex items-center gap-1"><Zap className="w-3 h-3" />{gap.jobs} jobs</span>
                {gap.salaryBoost && <span className="flex items-center gap-1"><TrendingUp className="w-3 h-3" />{gap.salaryBoost}</span>}
              </div>
              <button className={`w-full py-2.5 rounded-lg text-sm font-semibold transition-colors border-none cursor-pointer ${s.btn}`}>
                {gap.actionLabel}
              </button>
            </div>
          );
        })}
      </div>
      <Link to="/skills-gap" className="inline-flex items-center gap-1 text-primary-600 text-sm font-medium no-underline hover:underline mt-4">
        View All Skill Gaps <ArrowRight className="w-4 h-4" />
      </Link>
    </Section>
  );
}

/* ── Recent Activity ────────────────────────────────────────────── */

function RecentActivity() {
  const activities = [
    { icon: <CheckCircle2 className="w-4 h-4 text-emerald-600" />, bg: 'bg-emerald-100', text: 'Completed profile setup', time: '2 hours ago' },
    { icon: <Book className="w-4 h-4 text-blue-600" />, bg: 'bg-blue-100', text: 'Added skills to profile', time: 'Yesterday' },
    { icon: <Star className="w-4 h-4 text-amber-600" />, bg: 'bg-amber-100', text: 'Updated experience level', time: '2 days ago' },
    { icon: <Sparkles className="w-4 h-4 text-purple-600" />, bg: 'bg-purple-100', text: 'Identified skill gaps via AI', time: '3 days ago' },
    { icon: <Trophy className="w-4 h-4 text-yellow-600" />, bg: 'bg-yellow-100', text: 'Profile completion reached 80%', time: '5 days ago' },
  ];

  return (
    <Section title="Your Recent Activity" actionLabel="View All" actionTo="/activity">
      <div className="space-y-3">
        {activities.map((a, i) => (
          <div key={i} className="flex items-center gap-3">
            <div className={`w-8 h-8 ${a.bg} rounded-full flex items-center justify-center flex-shrink-0`}>
              {a.icon}
            </div>
            <p className="text-sm text-gray-700 flex-1">{a.text}</p>
            <span className="text-xs text-gray-400 dark:text-gray-500 whitespace-nowrap">{a.time}</span>
          </div>
        ))}
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
                  <p className="text-xs text-gray-500 dark:text-gray-400 dark:text-gray-500">{j.company}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400 dark:text-gray-500 mt-2">
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
    <div className="bg-gradient-to-r from-primary-50 via-purple-50 to-primary-50 rounded-2xl p-8 text-center">
      <Sparkles className="w-8 h-8 text-purple-500 mx-auto mb-3" />
      <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">Ready to accelerate your learning?</h2>
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-5 max-w-md mx-auto">
        Get personalized recommendations from our AI chatbot
      </p>
      <button className="inline-flex items-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-xl text-sm font-semibold hover:bg-primary-700 transition-colors border-none cursor-pointer shadow-lg shadow-primary-600/20">
        <MessageSquare className="w-4 h-4" />
        Chat Now
      </button>
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
  const { user, fetchUser } = useAuthStore();
  const [profile, setProfile] = useState(null);
  const [skills, setSkills] = useState([]);
  const [completion, setCompletion] = useState(null);
  const [careerStatus, setCareerStatus] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const load = async () => {
      try {
        if (!user) await fetchUser();

        const [summaryRes, statusRes] = await Promise.all([
          api.get('/users/profile/summary/'),
          api.get('/career/status/').catch(() => ({ data: {} })),
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
        setCareerStatus(statusRes.data);

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
        <WelcomeBanner user={user} profile={profile} completion={completion} />
        <QuickStats skills={skills} careerStatus={careerStatus} recommendations={recommendations} />

        <div className="grid lg:grid-cols-5 gap-6">
          <div className="lg:col-span-3 space-y-6">
            <YourSkills skills={skills} />
            <LearningRoadmap careerStatus={careerStatus} />
            <SkillsGapAnalysis profile={profile} recommendations={recommendations} />
          </div>
          <div className="lg:col-span-2 space-y-6">
            <RecentActivity />
            <RecommendedJobs />
          </div>
        </div>

        <BottomCTA />
      </div>
    </DashboardLayout>
  );
}
