import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Loader2 } from 'lucide-react';
import useAuthStore from '../store/authStore';
import useRecruiterGate from '../hooks/useRecruiterGate';
import RecruiterLayout from '../components/layout/RecruiterLayout';
import api from '../services/api';

export default function RecruiterSavedCandidatesPage() {
  const { t } = useTranslation();
  useRecruiterGate();
  const user = useAuthStore((s) => s.user);

  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const run = async () => {
      try {
        const { data } = await api.get('/recruiters/saved-candidates/');
        setRows(data.saved_candidates || []);
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
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{t('recruiter.savedCandidatesTitle')}</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {t('recruiter.savedCandidatesDesc')}
        </p>
      </div>

      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="w-8 h-8 text-primary-600 animate-spin" />
        </div>
      ) : rows.length === 0 ? (
        <div className="text-center py-16 text-gray-500 dark:text-gray-400 text-sm border border-dashed border-gray-200 dark:border-gray-800 rounded-xl">
          {t('recruiter.noSavedCandidates')}{' '}
          <Link to="/recruiter/candidates" className="text-primary-600 font-medium no-underline">
            {t('recruiter.searchTalent')}
          </Link>
        </div>
      ) : (
        <ul className="space-y-3">
          {rows.map((row) => {
            const c = row.candidate;
            return (
              <li
                key={row.saved_id}
                className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3"
              >
                <div className="min-w-0">
                  <Link
                    to={`/recruiter/candidates/${c?.id}`}
                    className="text-base font-semibold text-gray-900 dark:text-gray-100 hover:text-primary-600 no-underline"
                  >
                    {c?.full_name || 'Candidate'}
                  </Link>
                  <p className="text-sm text-gray-600 dark:text-gray-300">
                    {[c?.desired_role, c?.location].filter(Boolean).join(' · ') || '—'}
                  </p>
                  {row.notes ? (
                    <p className="text-xs text-gray-500 mt-2 italic">&ldquo;{row.notes}&rdquo;</p>
                  ) : null}
                </div>
                <Link
                  to={`/recruiter/candidates/${c?.id}`}
                  className="text-xs font-semibold text-primary-600 no-underline whitespace-nowrap"
                >
                  {t('recruiter.viewProfile')}
                </Link>
              </li>
            );
          })}
        </ul>
      )}
    </RecruiterLayout>
  );
}
