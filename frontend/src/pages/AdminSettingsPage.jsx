import { useEffect, useState } from 'react';
import { Loader2, ExternalLink } from 'lucide-react';
import AdminLayout from '../components/layout/AdminLayout';
import useAuthStore from '../store/authStore';
import useStaffGate from '../hooks/useStaffGate';
import api from '../services/api';

export default function AdminSettingsPage() {
  const { user, isStaff } = useStaffGate();
  const me = useAuthStore((s) => s.user) || user;

  const [platform, setPlatform] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isStaff) return;
    const run = async () => {
      try {
        const { data } = await api.get('/users/staff/settings/');
        setPlatform(data.platform || null);
      } catch {
        setPlatform(null);
      } finally {
        setLoading(false);
      }
    };
    run();
  }, [isStaff]);

  if (!me) {
    return (
      <AdminLayout user={me}>
        <Loader2 className="w-8 h-8 text-amber-600 animate-spin mx-auto mt-24" />
      </AdminLayout>
    );
  }

  return (
    <AdminLayout user={me}>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Platform settings</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Read-only hints exposed to staff. Sensitive secrets are not returned. Use Django for full configuration.
        </p>
      </div>

      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="w-8 h-8 text-amber-600 animate-spin" />
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-6 max-w-xl space-y-4 text-sm">
          <div className="flex justify-between gap-4">
            <span className="text-gray-500">DEBUG</span>
            <span className="font-mono text-gray-900 dark:text-gray-100">{String(platform?.debug)}</span>
          </div>
          <div className="flex justify-between gap-4">
            <span className="text-gray-500">DEFAULT_FROM_EMAIL</span>
            <span className="font-mono text-xs break-all text-gray-900 dark:text-gray-100">
              {platform?.default_from_email || '—'}
            </span>
          </div>
          <div>
            <span className="text-gray-500 block mb-1">ALLOWED_HOSTS (preview)</span>
            <pre className="text-xs bg-gray-50 dark:bg-gray-800 rounded-lg p-3 overflow-x-auto text-gray-800 dark:text-gray-200">
              {(platform?.allowed_hosts_preview || []).join(', ') || '—'}
            </pre>
          </div>
          <a
            href={(() => {
              const base = import.meta.env.VITE_API_BASE_URL || '/api/v1';
              if (typeof base === 'string' && base.startsWith('http')) {
                return `${base.replace(/\/api\/v1\/?$/i, '')}${platform?.django_admin_path || '/admin/'}`;
              }
              return `${window.location.origin}${platform?.django_admin_path || '/admin/'}`;
            })()}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 text-amber-700 dark:text-amber-400 font-semibold text-sm no-underline"
          >
            Open Django admin <ExternalLink className="w-4 h-4" />
          </a>
          <p className="text-xs text-gray-400 pt-2 border-t border-gray-100 dark:border-gray-800">
            Django admin usually runs on the same host as the API (e.g. http://localhost:8000/admin/). Adjust the link if
            your deployment differs.
          </p>
        </div>
      )}
    </AdminLayout>
  );
}
