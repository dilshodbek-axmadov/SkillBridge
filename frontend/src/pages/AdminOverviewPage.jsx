import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Users, Briefcase, Shield, Loader2, ArrowRight } from 'lucide-react';
import AdminLayout from '../components/layout/AdminLayout';
import useAuthStore from '../store/authStore';
import useStaffGate from '../hooks/useStaffGate';
import api from '../services/api';
import { safeGetItem } from '../utils/safeStorage';

function Stat({ label, value, icon: Icon }) {
  return (
    <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-5 flex gap-4">
      <div className="w-11 h-11 rounded-xl bg-amber-50 dark:bg-amber-950/40 flex items-center justify-center flex-shrink-0">
        <Icon className="w-5 h-5 text-amber-700 dark:text-amber-400" />
      </div>
      <div>
        <p className="text-2xl font-bold text-gray-900 dark:text-gray-100 tabular-nums">{value ?? '—'}</p>
        <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mt-0.5">{label}</p>
      </div>
    </div>
  );
}

export default function AdminOverviewPage() {
  const { user, fetchUser, isStaff } = useStaffGate();
  const storeUser = useAuthStore((s) => s.user);
  const effectiveUser = storeUser || user;

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!effectiveUser && safeGetItem('access_token')) {
      fetchUser();
    }
  }, [effectiveUser, fetchUser]);

  useEffect(() => {
    if (!effectiveUser) return;
    if (!isStaff) {
      setLoading(false);
      return;
    }
    const run = async () => {
      try {
        const { data: d } = await api.get('/users/staff/overview/');
        setData(d);
      } catch (e) {
        setError(e.response?.data?.detail || 'Could not load overview.');
      } finally {
        setLoading(false);
      }
    };
    run();
  }, [isStaff, effectiveUser]);

  if (!effectiveUser) {
    return (
      <AdminLayout user={null}>
        <div className="flex justify-center py-24">
          <Loader2 className="w-8 h-8 text-amber-600 animate-spin" />
        </div>
      </AdminLayout>
    );
  }

  return (
    <AdminLayout user={effectiveUser}>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Admin overview</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          High-level counts for users, recruiter plans, and job inventory. Use the workspace switcher to test developer
          and recruiter experiences.
        </p>
      </div>

      {error && (
        <div className="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-950/30 border border-red-200 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="w-8 h-8 text-amber-600 animate-spin" />
        </div>
      ) : (
        <>
          <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">Users</h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
            <Stat label="Total accounts" value={data?.users?.total} icon={Users} />
            <Stat label="Developers" value={data?.users?.developers} icon={Users} />
            <Stat label="Recruiters" value={data?.users?.recruiters} icon={Briefcase} />
            <Stat label="Recruiter Pro" value={data?.users?.recruiter_pro} icon={Shield} />
            <Stat label="Staff users" value={data?.users?.staff} icon={Shield} />
          </div>
          <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">Jobs index</h2>
          <div className="grid sm:grid-cols-2 gap-4 mb-10">
            <Stat label="Job postings (all)" value={data?.jobs?.total} icon={Briefcase} />
            <Stat label="Active listings" value={data?.jobs?.listing_active} icon={Briefcase} />
          </div>
          <div className="flex flex-wrap gap-3">
            <Link
              to="/admin-panel/users"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-amber-600 hover:bg-amber-700 text-white text-sm font-semibold no-underline"
            >
              Manage users &amp; plans <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              to="/admin-panel/tasks"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-800 dark:text-gray-200 text-sm font-semibold no-underline"
            >
              Background tasks
            </Link>
          </div>
        </>
      )}
    </AdminLayout>
  );
}
