import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  Zap,
  LayoutDashboard,
  Users,
  ServerCog,
  Settings,
  Menu,
  X,
  LogOut,
} from 'lucide-react';
import useAuthStore from '../../store/authStore';
import StaffWorkspaceSwitcher, { showStaffWorkspaceSwitcher } from '../StaffWorkspaceSwitcher';

const ADMIN_NAV = [
  { path: '/admin-panel', label: 'Overview', icon: LayoutDashboard, end: true },
  { path: '/admin-panel/users', label: 'Users & plans', icon: Users },
  { path: '/admin-panel/tasks', label: 'Background tasks', icon: ServerCog },
  { path: '/admin-panel/settings', label: 'Settings', icon: Settings },
];

function navActive(pathname, item) {
  if (item.end) {
    return pathname === item.path || pathname === `${item.path}/`;
  }
  return pathname === item.path || pathname.startsWith(`${item.path}/`);
}

function Sidebar({ user, mobileOpen, onClose }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useAuthStore();
  const firstName = user?.first_name || user?.email?.split('@')[0] || 'Admin';
  const initial = (user?.first_name?.[0] || user?.email?.[0] || 'A').toUpperCase();

  const handleLogout = async () => {
    await logout();
    onClose?.();
    navigate('/', { replace: true });
  };

  const navContent = (
    <div className="flex flex-col h-full">
      <div className="px-5 py-5 flex items-center gap-2.5">
        <div className="w-9 h-9 bg-gradient-to-br from-amber-500 to-orange-600 rounded-lg flex items-center justify-center flex-shrink-0">
          <Zap className="w-5 h-5 text-white" />
        </div>
        <div className="min-w-0">
          <span className="text-base font-bold text-gray-900 dark:text-gray-100 block leading-tight">
            Skill<span className="text-amber-600 dark:text-amber-400">Bridge</span>
          </span>
          <span className="text-[10px] font-semibold uppercase tracking-wide text-amber-700 dark:text-amber-400">
            Admin
          </span>
        </div>
      </div>

      {showStaffWorkspaceSwitcher(user) ? <StaffWorkspaceSwitcher /> : null}

      <nav className="flex-1 px-3 space-y-1 overflow-y-auto">
        {ADMIN_NAV.map((item) => {
          const active = navActive(location.pathname, item);
          const Icon = item.icon;
          return (
            <Link
              key={item.path}
              to={item.path}
              onClick={onClose}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium no-underline transition-colors ${
                active
                  ? 'bg-amber-100 dark:bg-amber-950/40 text-amber-900 dark:text-amber-200'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-gray-200'
              }`}
            >
              <Icon className={`w-[18px] h-[18px] flex-shrink-0 ${active ? 'text-amber-700 dark:text-amber-400' : 'text-gray-400'}`} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-gray-200 dark:border-gray-800 px-4 py-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-amber-100 dark:bg-amber-950/50 rounded-full flex items-center justify-center text-sm font-bold text-amber-800 dark:text-amber-300 flex-shrink-0">
            {initial}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">{firstName}</p>
            <p className="text-xs text-gray-400 truncate">{user?.email || ''}</p>
          </div>
          <button
            type="button"
            onClick={handleLogout}
            className="p-1.5 text-gray-400 hover:text-red-500 transition-colors bg-transparent border-none cursor-pointer"
            title="Logout"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <>
      <aside className="hidden lg:flex lg:flex-col lg:w-64 lg:fixed lg:inset-y-0 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 z-30">
        {navContent}
      </aside>
      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="fixed inset-0 bg-black/30" onClick={onClose} />
          <aside className="fixed inset-y-0 left-0 w-64 bg-white dark:bg-gray-900 shadow-xl z-50 flex flex-col">
            <button
              type="button"
              onClick={onClose}
              className="absolute top-4 right-4 p-1 text-gray-400 hover:text-gray-600 bg-transparent border-none cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
            {navContent}
          </aside>
        </div>
      )}
    </>
  );
}

export default function AdminLayout({ user, children }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const initial = (user?.first_name?.[0] || user?.email?.[0] || 'A').toUpperCase();

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 flex">
      <Sidebar user={user} mobileOpen={mobileMenuOpen} onClose={() => setMobileMenuOpen(false)} />
      <div className="flex-1 lg:ml-64">
        <header className="lg:hidden bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 px-4 py-3 flex items-center justify-between sticky top-0 z-20">
          <button
            type="button"
            onClick={() => setMobileMenuOpen(true)}
            className="p-1.5 text-gray-600 dark:text-gray-300 bg-transparent border-none cursor-pointer"
          >
            <Menu className="w-5 h-5" />
          </button>
          <span className="text-sm font-semibold text-amber-800 dark:text-amber-300">Admin</span>
          <div className="w-7 h-7 bg-amber-100 dark:bg-amber-950/50 rounded-full flex items-center justify-center text-xs font-bold text-amber-800">
            {initial}
          </div>
        </header>
        <main className="px-4 sm:px-6 lg:px-8 py-6 sm:py-8 max-w-6xl">{children}</main>
      </div>
    </div>
  );
}
