import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Loader2, AlertCircle, ChevronLeft, ChevronRight } from 'lucide-react';
import DashboardLayout from '../components/layout/DashboardLayout';
import useAuthStore from '../store/authStore';
import api from '../services/api';
import { formatRelativeTime, getActivityVisual } from '../utils/activityFeed';

export default function ActivityPage() {
  const { user, fetchUser } = useAuthStore();
  const [rows, setRows] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [total, setTotal] = useState(0);
  const [pageSize] = useState(15);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const load = async () => {
      try {
        if (!user) await fetchUser();
        const { data } = await api.get('/users/profile/activity/', {
          params: { page, page_size: pageSize },
        });
        setRows(data.results || []);
        setTotalPages(data.total_pages || 0);
        setTotal(data.count ?? 0);
      } catch (err) {
        if (err.response?.status === 401) {
          window.location.href = '/login?redirect=/activity';
          return;
        }
        setError('Could not load activity.');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [user, fetchUser, page, pageSize]);

  return (
    <DashboardLayout user={user}>
      <div className="max-w-3xl mx-auto space-y-6">
        <div>
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-1 text-sm text-primary-600 font-medium no-underline hover:underline mb-2"
          >
            <ChevronLeft className="w-4 h-4" />
            Back to dashboard
          </Link>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Activity</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Things you&apos;ve done on SkillBridge{total > 0 ? ` · ${total} total` : ''}
          </p>
        </div>

        <section className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-6">
          {loading && (
            <div className="flex justify-center py-16">
              <Loader2 className="w-8 h-8 text-primary-600 animate-spin" />
            </div>
          )}

          {error && !loading && (
            <div className="flex flex-col items-center py-12 text-center">
              <AlertCircle className="w-10 h-10 text-red-400 mb-3" />
              <p className="text-gray-600 dark:text-gray-300">{error}</p>
            </div>
          )}

          {!loading && !error && rows.length === 0 && (
            <p className="text-center text-gray-500 dark:text-gray-400 py-12 text-sm">
              No activity yet. Complete your profile, run a skill gap analysis, or update your roadmap to see entries here.
            </p>
          )}

          {!loading && !error && rows.length > 0 && (
            <ul className="space-y-4">
              {rows.map((a) => {
                const v = getActivityVisual(a.activity_type);
                const Icon = v.Icon;
                const inner = (
                  <div className="flex items-start gap-3">
                    <div
                      className={`w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 ${v.bg}`}
                    >
                      <Icon className={`w-4 h-4 ${v.iconClass}`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-800 dark:text-gray-200">{a.description}</p>
                      <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
                        {formatRelativeTime(a.created_at)}
                      </p>
                    </div>
                  </div>
                );

                return (
                  <li
                    key={a.activity_id}
                    className="border-b border-gray-100 dark:border-gray-800 pb-4 last:border-0 last:pb-0"
                  >
                    {a.link_path ? (
                      <Link to={a.link_path} className="block no-underline hover:opacity-90">
                        {inner}
                      </Link>
                    ) : (
                      inner
                    )}
                  </li>
                );
              })}
            </ul>
          )}

          {!loading && !error && totalPages > 1 && (
            <div className="flex items-center justify-between mt-6 pt-4 border-t border-gray-100 dark:border-gray-800">
              <button
                type="button"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="inline-flex items-center gap-1 px-3 py-2 text-sm font-medium rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 disabled:opacity-40 cursor-pointer disabled:cursor-not-allowed"
              >
                <ChevronLeft className="w-4 h-4" />
                Previous
              </button>
              <span className="text-xs text-gray-500">
                Page {page} of {totalPages}
              </span>
              <button
                type="button"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
                className="inline-flex items-center gap-1 px-3 py-2 text-sm font-medium rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 disabled:opacity-40 cursor-pointer disabled:cursor-not-allowed"
              >
                Next
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </section>
      </div>
    </DashboardLayout>
  );
}
