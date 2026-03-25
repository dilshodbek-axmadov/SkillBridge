import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  Zap, TrendingUp, Briefcase, BarChart3, MessageSquare,
  Home, Map, Lightbulb, FileText, Settings,
  Menu, X, LogOut, ServerCog,
} from 'lucide-react';
import useAuthStore from '../../store/authStore';
import StaffWorkspaceSwitcher, { showStaffWorkspaceSwitcher } from '../StaffWorkspaceSwitcher';

const NAV_ITEMS = [
  { path: '/dashboard',        label: 'Dashboard',          icon: Home },
  { path: '/roadmap',          label: 'Learning Roadmap',   icon: Map },
  { path: '/skills-gap',       label: 'Skills Gap Analysis',icon: BarChart3 },
  { path: '/project-ideas',    label: 'Project Ideas',      icon: Lightbulb },
  { path: '/jobs',             label: 'Jobs',               icon: Briefcase },
  { path: '/market-analytics', label: 'Market Analytics',   icon: TrendingUp },
  { path: '/cv-builder',       label: 'CV Builder',         icon: FileText },
  { path: '/chat',             label: 'AI Chatbot',         icon: MessageSquare },
  { path: '/settings',         label: 'Settings',           icon: Settings },
];

const ADMIN_NAV_ITEMS = [
  { path: '/background-tasks', label: 'Background Tasks',   icon: ServerCog },
];

function Sidebar({ user, mobileOpen, onClose }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useAuthStore();
  const firstName = user?.first_name || user?.email?.split('@')[0] || 'User';
  const initial = (user?.first_name?.[0] || user?.email?.[0] || 'U').toUpperCase();

  const handleLogout = async () => {
    await logout();
    onClose?.();
    navigate('/', { replace: true });
  };

  const navContent = (
    <div className="flex flex-col h-full">
      <div className="px-5 py-5 flex items-center gap-2.5">
        <div className="w-9 h-9 bg-gradient-to-br from-primary-600 to-purple-500 rounded-lg flex items-center justify-center flex-shrink-0">
          <Zap className="w-5 h-5 text-white" />
        </div>
        <span className="text-base font-bold text-gray-900 dark:text-gray-100">
          Skill<span className="text-primary-600 dark:text-primary-400">Bridge</span>
        </span>
      </div>

      {showStaffWorkspaceSwitcher(user) ? <StaffWorkspaceSwitcher /> : null}

      <nav className="flex-1 px-3 mt-2 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map((item) => {
          const active = location.pathname === item.path;
          const Icon = item.icon;
          return (
            <Link
              key={item.path}
              to={item.path}
              onClick={onClose}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium no-underline transition-colors ${
                active
                  ? 'bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-gray-200'
              }`}
            >
              <Icon className={`w-[18px] h-[18px] flex-shrink-0 ${active ? 'text-primary-600 dark:text-primary-400' : 'text-gray-400 dark:text-gray-500'}`} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-gray-200 dark:border-gray-800 px-4 py-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-primary-100 dark:bg-primary-900/40 rounded-full flex items-center justify-center text-sm font-bold text-primary-700 dark:text-primary-400 flex-shrink-0">
            {initial}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">{firstName}</p>
            <p className="text-xs text-gray-400 dark:text-gray-500 truncate">{user?.email || ''}</p>
          </div>
          <button
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
              onClick={onClose}
              className="absolute top-4 right-4 p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 bg-transparent border-none cursor-pointer"
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

export default function DashboardLayout({ user, children }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const initial = (user?.first_name?.[0] || user?.email?.[0] || 'U').toUpperCase();

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 flex">
      <Sidebar user={user} mobileOpen={mobileMenuOpen} onClose={() => setMobileMenuOpen(false)} />

      <div className="flex-1 lg:ml-64">
        <header className="lg:hidden bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 px-4 py-3 flex items-center justify-between sticky top-0 z-20">
          <button
            onClick={() => setMobileMenuOpen(true)}
            className="p-1.5 text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white bg-transparent border-none cursor-pointer"
          >
            <Menu className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 bg-gradient-to-br from-primary-600 to-purple-500 rounded-lg flex items-center justify-center">
              <Zap className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="text-sm font-semibold text-gray-900 dark:text-gray-100">
              Skill<span className="text-primary-600 dark:text-primary-400">Bridge</span>
            </span>
          </div>
          <div className="w-7 h-7 bg-primary-100 dark:bg-primary-900/40 rounded-full flex items-center justify-center text-xs font-bold text-primary-700 dark:text-primary-400">
            {initial}
          </div>
        </header>

        <main className="px-4 sm:px-6 lg:px-8 py-6 sm:py-8 max-w-6xl">
          {children}
        </main>
      </div>
    </div>
  );
}
