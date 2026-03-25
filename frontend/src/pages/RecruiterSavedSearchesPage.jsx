import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import useAuthStore from '../store/authStore';
import useRecruiterGate from '../hooks/useRecruiterGate';
import RecruiterLayout from '../components/layout/RecruiterLayout';
import api from '../services/api';

function filtersToQuery(filters) {
  if (!filters || typeof filters !== 'object') return '';
  const p = new URLSearchParams();
  Object.entries(filters).forEach(([k, v]) => {
    if (v !== undefined && v !== null && String(v).trim() !== '') p.set(k, String(v));
  });
  const s = p.toString();
  return s ? `?${s}` : '';
}

export default function RecruiterSavedSearchesPage() {
  useRecruiterGate();
  const user = useAuthStore((s) => s.user);

  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const run = async () => {
      try {
        const { data } = await api.get('/recruiters/saved-searches/');
        setRows(data.saved_searches || []);
      } catch {
        setRows([]);
      } finally {
        setLoading(false);
      }
    };
    run();
  }, []);

  return (
    <RecruiterLayout user={user}>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Saved searches</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Re-run candidate searches with one click. Filters map to the find-candidates API (q, location, skill, etc.).
        </p>
      </div>

      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="w-8 h-8 text-primary-600 animate-spin" />
        </div>
      ) : rows.length === 0 ? (
        <div className="text-center py-16 text-gray-500 dark:text-gray-400 text-sm border border-dashed border-gray-200 dark:border-gray-800 rounded-xl">
          No saved searches yet. Save a search from the API or add one later; for now{' '}
          <Link to="/recruiter/candidates" className="text-primary-600 font-medium no-underline">
            open find candidates
          </Link>
          .
        </div>
      ) : (
        <ul className="space-y-3">
          {rows.map((s) => {
            const qs = filtersToQuery(s.filters);
            return (
              <li
                key={s.search_id}
                className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3"
              >
                <div>
                  <p className="font-semibold text-gray-900 dark:text-gray-100">{s.name}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 font-mono">
                    {s.filters && Object.keys(s.filters).length
                      ? JSON.stringify(s.filters)
                      : 'No filters stored'}
                  </p>
                </div>
                <Link
                  to={`/recruiter/candidates${qs}`}
                  className="text-xs font-semibold text-primary-600 no-underline whitespace-nowrap"
                >
                  Run search →
                </Link>
              </li>
            );
          })}
        </ul>
      )}
    </RecruiterLayout>
  );
}
