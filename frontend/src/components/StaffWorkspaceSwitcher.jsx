import { Link, useLocation } from 'react-router-dom';
import { Code2, Briefcase, Shield } from 'lucide-react';

const MODES = [
  { id: 'developer', label: 'Developer', path: '/dashboard', icon: Code2 },
  { id: 'recruiter', label: 'Recruiter', path: '/recruiter/dashboard', icon: Briefcase },
  { id: 'admin', label: 'Admin', path: '/admin-panel', icon: Shield },
];

function activeMode(pathname) {
  if (pathname.startsWith('/admin-panel')) return 'admin';
  if (pathname.startsWith('/recruiter')) return 'recruiter';
  return 'developer';
}

/**
 * Lets staff/superusers jump between developer app, recruiter app, and in-app admin.
 */
export default function StaffWorkspaceSwitcher() {
  const location = useLocation();
  const current = activeMode(location.pathname);

  return (
    <div className="px-3 mb-3 pb-3 border-b border-amber-200/60 dark:border-amber-900/40">
      <p className="text-[10px] font-bold uppercase tracking-wider text-amber-800 dark:text-amber-400 mb-2 px-1">
        Staff workspace
      </p>
      <div className="flex flex-col gap-1">
        {MODES.map((m) => {
          const Icon = m.icon;
          const on = m.id === current;
          return (
            <Link
              key={m.id}
              to={m.path}
              className={`flex items-center gap-2 px-2.5 py-2 rounded-lg text-xs font-semibold no-underline transition-colors ${
                on
                  ? 'bg-amber-100 dark:bg-amber-950/50 text-amber-900 dark:text-amber-200 ring-1 ring-amber-300/60 dark:ring-amber-800'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-gray-100'
              }`}
            >
              <Icon className="w-3.5 h-3.5 flex-shrink-0" />
              {m.label}
            </Link>
          );
        })}
      </div>
    </div>
  );
}

export function showStaffWorkspaceSwitcher(user) {
  return !!(user?.is_staff || user?.is_superuser);
}
