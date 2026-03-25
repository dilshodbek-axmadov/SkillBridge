import { useCallback, useEffect, useState } from 'react';
import { Loader2, Pencil, ChevronLeft, ChevronRight } from 'lucide-react';
import AdminLayout from '../components/layout/AdminLayout';
import useAuthStore from '../store/authStore';
import useStaffGate from '../hooks/useStaffGate';
import api from '../services/api';

export default function AdminUsersPage() {
  const { user, fetchUser, isStaff } = useStaffGate();
  const me = useAuthStore((s) => s.user) || user;

  const [results, setResults] = useState([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [q, setQ] = useState('');
  const [userType, setUserType] = useState('');
  const [planFilter, setPlanFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editOpen, setEditOpen] = useState(null);
  const [saveLoading, setSaveLoading] = useState(false);

  const load = useCallback(async () => {
    if (!isStaff) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError('');
    try {
      const params = { page, page_size: pageSize };
      if (q.trim()) params.q = q.trim();
      if (userType) params.user_type = userType;
      if (planFilter) params.recruiter_plan = planFilter;
      const { data } = await api.get('/users/staff/users/', { params });
      setResults(data.results || []);
      setCount(data.count || 0);
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to load users.');
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, [isStaff, page, pageSize, q, userType, planFilter]);

  useEffect(() => {
    load();
  }, [load]);

  const totalPages = Math.max(1, Math.ceil(count / pageSize));

  const handleSave = async (payload) => {
    if (!editOpen) return;
    setSaveLoading(true);
    try {
      await api.patch(`/users/staff/users/${editOpen.id}/`, payload);
      setEditOpen(null);
      await load();
    } catch (e) {
      const msg = e.response?.data?.error || Object.values(e.response?.data || {})?.[0]?.[0] || 'Save failed';
      alert(typeof msg === 'string' ? msg : 'Save failed');
    } finally {
      setSaveLoading(false);
    }
  };

  if (!me) {
    return (
      <AdminLayout user={me}>
        <div className="flex justify-center py-24">
          <Loader2 className="w-8 h-8 text-amber-600 animate-spin" />
        </div>
      </AdminLayout>
    );
  }

  return (
    <AdminLayout user={me}>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Users &amp; subscriptions</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Search accounts, change recruiter plan (Pro / Free), role, and active state. Staff flags require a superuser.
        </p>
      </div>

      <div className="flex flex-col lg:flex-row gap-3 mb-4">
        <input
          type="search"
          placeholder="Search email, username, name…"
          value={q}
          onChange={(e) => { setQ(e.target.value); setPage(1); }}
          className="flex-1 px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
        />
        <select
          value={userType}
          onChange={(e) => { setUserType(e.target.value); setPage(1); }}
          className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
        >
          <option value="">All types</option>
          <option value="developer">Developer</option>
          <option value="recruiter">Recruiter</option>
        </select>
        <select
          value={planFilter}
          onChange={(e) => { setPlanFilter(e.target.value); setPage(1); }}
          className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
        >
          <option value="">All plans</option>
          <option value="free">Free</option>
          <option value="pro">Pro</option>
        </select>
      </div>

      {error && (
        <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-700">{error}</div>
      )}

      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="w-8 h-8 text-amber-600 animate-spin" />
        </div>
      ) : (
        <>
          <div className="overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-800 text-left text-xs uppercase text-gray-500">
                  <th className="px-3 py-2">User</th>
                  <th className="px-3 py-2">Type</th>
                  <th className="px-3 py-2">Plan</th>
                  <th className="px-3 py-2">Active</th>
                  <th className="px-3 py-2">Flags</th>
                  <th className="px-3 py-2 w-24" />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                {results.map((row) => (
                  <tr key={row.id} className="hover:bg-gray-50/80 dark:hover:bg-gray-800/50">
                    <td className="px-3 py-2">
                      <p className="font-medium text-gray-900 dark:text-gray-100">{row.full_name || row.username}</p>
                      <p className="text-xs text-gray-500">{row.email}</p>
                    </td>
                    <td className="px-3 py-2 capitalize">{row.user_type}</td>
                    <td className="px-3 py-2 capitalize">{row.recruiter_plan}</td>
                    <td className="px-3 py-2">{row.is_active ? 'Yes' : 'No'}</td>
                    <td className="px-3 py-2 text-xs text-gray-500">
                      {[row.is_staff && 'staff', row.is_superuser && 'superuser'].filter(Boolean).join(', ') || '—'}
                    </td>
                    <td className="px-3 py-2">
                      <button
                        type="button"
                        onClick={() => setEditOpen(row)}
                        className="inline-flex items-center gap-1 text-amber-700 dark:text-amber-400 font-semibold text-xs bg-transparent border-none cursor-pointer"
                      >
                        <Pencil className="w-3.5 h-3.5" />
                        Edit
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between mt-4 text-sm text-gray-600">
            <span>
              {count} users · page {page} / {totalPages}
            </span>
            <div className="flex gap-2">
              <button
                type="button"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 disabled:opacity-40 bg-white dark:bg-gray-800 cursor-pointer"
              >
                <ChevronLeft className="w-4 h-4" /> Prev
              </button>
              <button
                type="button"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
                className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 disabled:opacity-40 bg-white dark:bg-gray-800 cursor-pointer"
              >
                Next <ChevronRight className="w-4 h-4" />
                </button>
            </div>
          </div>
        </>
      )}

      {editOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40">
          <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-xl max-w-md w-full p-6">
            <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-1">Edit user</h3>
            <p className="text-xs text-gray-500 mb-4">{editOpen.email}</p>
            <div className="space-y-3">
              <label className="block text-xs font-medium text-gray-600">
                User type
                <select
                  id="edit-user-type"
                  defaultValue={editOpen.user_type}
                  className="mt-1 w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
                >
                  <option value="developer">developer</option>
                  <option value="recruiter">recruiter</option>
                </select>
              </label>
              <label className="block text-xs font-medium text-gray-600">
                Recruiter plan (subscription)
                <select
                  id="edit-plan"
                  defaultValue={editOpen.recruiter_plan}
                  className="mt-1 w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
                >
                  <option value="free">free</option>
                  <option value="pro">pro</option>
                </select>
              </label>
              <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                <input type="checkbox" id="edit-active" defaultChecked={editOpen.is_active} className="rounded" />
                Active (can log in)
              </label>
              {!!me?.is_superuser && (
                <>
                  <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                    <input type="checkbox" id="edit-staff" defaultChecked={editOpen.is_staff} className="rounded" />
                    Staff (Django admin / APIs)
                  </label>
                  <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                    <input type="checkbox" id="edit-super" defaultChecked={editOpen.is_superuser} className="rounded" />
                    Superuser
                  </label>
                </>
              )}
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button
                type="button"
                onClick={() => setEditOpen(null)}
                className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-sm font-semibold bg-transparent cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={saveLoading}
                onClick={() => {
                  const utEl = document.getElementById('edit-user-type');
                  const planEl = document.getElementById('edit-plan');
                  const payload = {
                    user_type: utEl?.value,
                    recruiter_plan: planEl?.value,
                    is_active: document.getElementById('edit-active')?.checked,
                  };
                  if (me?.is_superuser) {
                    payload.is_staff = document.getElementById('edit-staff')?.checked;
                    payload.is_superuser = document.getElementById('edit-super')?.checked;
                  }
                  handleSave(payload);
                }}
                className="px-4 py-2 rounded-lg bg-amber-600 hover:bg-amber-700 text-white text-sm font-semibold border-none cursor-pointer disabled:opacity-50"
              >
                {saveLoading ? 'Saving…' : 'Save'}
              </button>
            </div>
          </div>
        </div>
      )}
    </AdminLayout>
  );
}
