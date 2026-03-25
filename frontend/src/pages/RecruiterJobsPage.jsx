import { useEffect, useState } from 'react';
import { Loader2 } from 'lucide-react';
import useAuthStore from '../store/authStore';
import useRecruiterGate from '../hooks/useRecruiterGate';
import RecruiterLayout from '../components/layout/RecruiterLayout';
import api from '../services/api';

export default function RecruiterJobsPage() {
  useRecruiterGate();
  const user = useAuthStore((s) => s.user);

  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const run = async () => {
      try {
        const { data } = await api.get('/recruiters/jobs/');
        setJobs(data.jobs || []);
      } catch {
        setJobs([]);
      } finally {
        setLoading(false);
      }
    };
    run();
  }, []);

  return (
    <RecruiterLayout user={user}>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">My job posts</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Roles you publish on SkillBridge (<code className="text-xs bg-gray-100 dark:bg-gray-800 px-1 rounded">source=platform</code>
          ). Create and edit via API or a future form.
        </p>
      </div>

      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="w-8 h-8 text-primary-600 animate-spin" />
        </div>
      ) : jobs.length === 0 ? (
        <div className="text-center py-16 text-gray-500 dark:text-gray-400 text-sm border border-dashed border-gray-200 dark:border-gray-800 rounded-xl">
          You have not posted a job yet. Use{' '}
          <code className="text-xs bg-gray-100 dark:bg-gray-800 px-1 rounded">POST /api/v1/recruiters/jobs/</code> or ask
          your team to wire the publish form.
        </div>
      ) : (
        <ul className="space-y-3">
          {jobs.map((job) => (
            <li
              key={job.job_id}
              id={`job-${job.job_id}`}
              className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4 sm:p-5 scroll-mt-24"
            >
              <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2">
                <div>
                  <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100">{job.job_title}</h2>
                  <p className="text-sm text-gray-600 dark:text-gray-300 mt-0.5">
                    {[job.company_name, job.location, job.employment_type].filter(Boolean).join(' · ')}
                  </p>
                </div>
                <span
                  className={`text-xs font-semibold px-2.5 py-1 rounded-md w-fit ${
                    job.is_active
                      ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300'
                      : 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'
                  }`}
                >
                  {job.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
              {job.job_description && (
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-3 line-clamp-3">{job.job_description}</p>
              )}
            </li>
          ))}
        </ul>
      )}
    </RecruiterLayout>
  );
}
