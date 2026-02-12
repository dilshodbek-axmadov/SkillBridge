import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Loader2, Zap, Trophy, TrendingUp, Briefcase, Star,
  ChevronRight, RefreshCw, ArrowRight, CheckCircle2, Sparkles,
} from 'lucide-react';
import api from '../services/api';

const DEMAND_CONFIG = {
  very_high: { label: 'Very High Demand', color: 'text-green-700 bg-green-50 border-green-200' },
  high: { label: 'High Demand', color: 'text-emerald-700 bg-emerald-50 border-emerald-200' },
  medium: { label: 'Medium Demand', color: 'text-yellow-700 bg-yellow-50 border-yellow-200' },
  low: { label: 'Low Demand', color: 'text-gray-600 bg-gray-50 border-gray-200' },
};

const DIFFICULTY_CONFIG = {
  beginner: { label: 'Beginner Friendly', color: 'text-green-700' },
  intermediate: { label: 'Intermediate', color: 'text-yellow-700' },
  advanced: { label: 'Advanced', color: 'text-red-600' },
};

function getMatchColor(score) {
  if (score >= 80) return 'from-green-500 to-emerald-500';
  if (score >= 60) return 'from-primary-500 to-primary-600';
  if (score >= 40) return 'from-yellow-500 to-orange-500';
  return 'from-gray-400 to-gray-500';
}

function getMatchBadge(rank) {
  if (rank === 1) return { icon: Trophy, label: 'Best Match', color: 'text-yellow-600 bg-yellow-50 border-yellow-200' };
  if (rank === 2) return { icon: Star, label: 'Great Fit', color: 'text-primary-600 bg-primary-50 border-primary-200' };
  if (rank === 3) return { icon: TrendingUp, label: 'Good Option', color: 'text-purple-600 bg-purple-50 border-purple-200' };
  return { icon: Briefcase, label: 'Consider', color: 'text-gray-600 bg-gray-50 border-gray-200' };
}

function formatSalary(amount) {
  if (!amount) return null;
  const num = parseFloat(amount);
  if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(1)}M UZS`;
  if (num >= 1_000) return `${(num / 1_000).toFixed(0)}K UZS`;
  return `${num} UZS`;
}

export default function RecommendationsPage() {
  const navigate = useNavigate();
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selecting, setSelecting] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchRecommendations = async () => {
      try {
        const { data } = await api.get('/career/recommendations/');
        const recs = data.recommendations || [];
        setRecommendations(recs);

        // Check if user already selected a role
        const alreadySelected = recs.find((r) => r.user_selected);
        if (alreadySelected) setSelectedId(alreadySelected.id);

        if (recs.length === 0) {
          setError('No recommendations found. Please take the assessment first.');
        }
      } catch (err) {
        if (err.response?.status === 401) {
          navigate('/login?redirect=/recommendations', { replace: true });
          return;
        }
        setError('Failed to load recommendations. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchRecommendations();
  }, [navigate]);

  const handleSelectRole = async (recommendationId) => {
    setSelecting(recommendationId);
    try {
      await api.post('/career/select-role/', { recommendation_id: recommendationId });
      setSelectedId(recommendationId);
      setRecommendations((prev) =>
        prev.map((r) => ({
          ...r,
          user_selected: r.id === recommendationId,
        }))
      );
    } catch {
      setError('Failed to select role. Please try again.');
    } finally {
      setSelecting(null);
    }
  };

  // Loading
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-10 h-10 text-primary-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-500 dark:text-gray-400 text-sm">Loading your career recommendations...</p>
        </div>
      </div>
    );
  }

  // No recommendations
  if (error && recommendations.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
        <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-800 p-10 max-w-md text-center">
          <div className="w-16 h-16 bg-primary-50 rounded-2xl flex items-center justify-center mx-auto mb-5">
            <Sparkles className="w-8 h-8 text-primary-500" />
          </div>
          <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">No Results Yet</h2>
          <p className="text-gray-500 dark:text-gray-400 text-sm mb-6">{error}</p>
          <Link
            to="/assessment"
            className="inline-flex items-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-lg text-sm font-semibold hover:bg-primary-700 transition-colors no-underline"
          >
            Take Assessment
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-8 h-8 bg-gradient-to-br from-primary-600 to-purple-500 rounded-lg flex items-center justify-center">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <span className="text-sm font-semibold text-gray-500 dark:text-gray-400 dark:text-gray-500">SkillBridge</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            Your Career Matches
          </h1>
          <p className="text-gray-500 text-lg">
            Based on your interests and aptitudes, here are the best IT career paths for you.
          </p>
        </div>
      </header>

      {/* Results */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-10">
        {/* Error inline */}
        {error && recommendations.length > 0 && (
          <div className="mb-6 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 rounded-lg text-sm text-red-600 text-center">
            {error}
          </div>
        )}

        {/* Recommendation cards */}
        <div className="space-y-5">
          {recommendations.map((rec) => {
            const role = rec.role;
            const matchColor = getMatchColor(rec.match_score);
            const badge = getMatchBadge(rec.rank);
            const BadgeIcon = badge.icon;
            const demand = DEMAND_CONFIG[role.job_demand] || DEMAND_CONFIG.medium;
            const difficulty = DIFFICULTY_CONFIG[role.difficulty_level] || DIFFICULTY_CONFIG.beginner;
            const salary = formatSalary(role.avg_salary_uzs);
            const isSelected = rec.id === selectedId;
            const isSelecting = selecting === rec.id;

            return (
              <div
                key={rec.id}
                className={`bg-white rounded-2xl border-2 transition-all shadow-sm hover:shadow-md ${
                  isSelected
                    ? 'border-primary-500 shadow-md shadow-primary-100'
                    : 'border-gray-200'
                }`}
              >
                <div className="p-6 sm:p-8">
                  {/* Top row: rank badge + match score */}
                  <div className="flex items-start justify-between mb-5">
                    <div className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs font-semibold ${badge.color}`}>
                      <BadgeIcon className="w-3.5 h-3.5" />
                      {badge.label}
                    </div>

                    {/* Match score circle */}
                    <div className="flex items-center gap-3">
                      <div className="text-right">
                        <p className="text-xs text-gray-400 leading-none mb-1">Match</p>
                        <p className="text-2xl font-bold text-gray-900 dark:text-gray-100 leading-none">
                          {Math.round(rec.match_score)}%
                        </p>
                      </div>
                      <div className="w-14 h-14 relative">
                        <svg className="w-14 h-14 -rotate-90" viewBox="0 0 56 56">
                          <circle
                            cx="28" cy="28" r="24"
                            fill="none"
                            stroke="#e5e7eb"
                            strokeWidth="4"
                          />
                          <circle
                            cx="28" cy="28" r="24"
                            fill="none"
                            stroke="url(#matchGrad)"
                            strokeWidth="4"
                            strokeLinecap="round"
                            strokeDasharray={`${(rec.match_score / 100) * 150.8} 150.8`}
                          />
                          <defs>
                            <linearGradient id="matchGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                              <stop offset="0%" stopColor="#3b82f6" />
                              <stop offset="100%" stopColor="#10b981" />
                            </linearGradient>
                          </defs>
                        </svg>
                      </div>
                    </div>
                  </div>

                  {/* Role name + description */}
                  <h2 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                    {role.name}
                  </h2>
                  <p className="text-gray-500 dark:text-gray-400 text-sm leading-relaxed mb-4">
                    {role.description}
                  </p>

                  {/* Meta tags */}
                  <div className="flex flex-wrap gap-2 mb-5">
                    <span className={`inline-flex items-center px-3 py-1 rounded-full border text-xs font-medium ${demand.color}`}>
                      {demand.label}
                    </span>
                    <span className={`inline-flex items-center px-3 py-1 rounded-full border text-xs font-medium border-gray-200 bg-gray-50 ${difficulty.color}`}>
                      {difficulty.label}
                    </span>
                    {salary && (
                      <span className="inline-flex items-center px-3 py-1 rounded-full border border-gray-200 bg-gray-50 text-xs font-medium text-gray-600">
                        ~{salary}/mo
                      </span>
                    )}
                  </div>

                  {/* AI reasoning */}
                  {rec.reasoning && (
                    <div className="bg-gray-50 rounded-xl p-4 mb-5 border border-gray-100">
                      <div className="flex items-center gap-1.5 mb-2">
                        <Sparkles className="w-3.5 h-3.5 text-purple-500" />
                        <span className="text-xs font-semibold text-purple-600">AI Insight</span>
                      </div>
                      <p className="text-sm text-gray-600 leading-relaxed">{rec.reasoning}</p>
                    </div>
                  )}

                  {/* Action button */}
                  <div className="flex items-center gap-3">
                    {isSelected ? (
                      <div className="inline-flex items-center gap-2 px-5 py-2.5 bg-primary-50 text-primary-700 rounded-lg text-sm font-semibold border border-primary-200">
                        <CheckCircle2 className="w-4 h-4" />
                        Selected as Your Path
                      </div>
                    ) : (
                      <button
                        onClick={() => handleSelectRole(rec.id)}
                        disabled={isSelecting}
                        className="inline-flex items-center gap-2 px-5 py-2.5 bg-primary-600 text-white rounded-lg text-sm font-semibold hover:bg-primary-700 transition-colors cursor-pointer border-none disabled:bg-primary-400"
                      >
                        {isSelecting ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            Selecting...
                          </>
                        ) : (
                          <>
                            Choose This Path
                            <ChevronRight className="w-4 h-4" />
                          </>
                        )}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Bottom actions */}
        <div className="mt-10 flex flex-col sm:flex-row items-center justify-between gap-4 pt-8 border-t border-gray-200">
          <Link
            to="/assessment"
            className="inline-flex items-center gap-2 text-sm font-medium text-gray-500 hover:text-primary-600 transition-colors no-underline"
          >
            <RefreshCw className="w-4 h-4" />
            Retake Assessment
          </Link>

          {selectedId && (
            <Link
              to="/dashboard"
              className="inline-flex items-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-lg text-sm font-semibold hover:bg-primary-700 transition-colors no-underline"
            >
              Go to Dashboard
              <ArrowRight className="w-4 h-4" />
            </Link>
          )}
        </div>
      </main>
    </div>
  );
}
