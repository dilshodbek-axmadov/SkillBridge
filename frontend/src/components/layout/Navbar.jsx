import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Menu, X, Zap } from 'lucide-react';
import useAuthStore from '../../store/authStore';

export default function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const { isAuthenticated, logout } = useAuthStore();

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 no-underline">
            <div className="w-8 h-8 bg-gradient-to-br from-primary-600 to-purple-500 rounded-lg flex items-center justify-center">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-gray-900">
              Skill<span className="text-primary-600">Bridge</span>
            </span>
          </Link>

          {/* Desktop nav */}
          <div className="hidden md:flex items-center gap-8">
            <Link to="/" className="text-sm font-medium text-gray-600 hover:text-primary-600 no-underline transition-colors">
              Home
            </Link>
            <Link to="/dashboard" className="text-sm font-medium text-gray-600 hover:text-primary-600 no-underline transition-colors">
              Dashboard
            </Link>
            <Link to="/roadmap" className="text-sm font-medium text-gray-600 hover:text-primary-600 no-underline transition-colors">
              Roadmap
            </Link>
            <Link to="/projects" className="text-sm font-medium text-gray-600 hover:text-primary-600 no-underline transition-colors">
              Projects
            </Link>
          </div>

          {/* Auth buttons */}
          <div className="hidden md:flex items-center gap-3">
            {isAuthenticated ? (
              <>
                <Link
                  to="/profile"
                  className="text-sm font-medium text-gray-700 hover:text-primary-600 no-underline transition-colors"
                >
                  Profile
                </Link>
                <button
                  onClick={logout}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors cursor-pointer border-none"
                >
                  Log out
                </button>
              </>
            ) : (
              <>
                <Link
                  to="/login"
                  className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-primary-600 no-underline transition-colors"
                >
                  Log in
                </Link>
                <Link
                  to="/register"
                  className="px-5 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 no-underline transition-colors"
                >
                  Sign up
                </Link>
              </>
            )}
          </div>

          {/* Mobile toggle */}
          <button
            className="md:hidden p-2 text-gray-600 hover:text-gray-900 bg-transparent border-none cursor-pointer"
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden bg-white border-t border-gray-200 px-4 py-4 space-y-3">
          <Link to="/" className="block text-sm font-medium text-gray-600 no-underline py-2" onClick={() => setMobileOpen(false)}>Home</Link>
          <Link to="/dashboard" className="block text-sm font-medium text-gray-600 no-underline py-2" onClick={() => setMobileOpen(false)}>Dashboard</Link>
          <Link to="/roadmap" className="block text-sm font-medium text-gray-600 no-underline py-2" onClick={() => setMobileOpen(false)}>Roadmap</Link>
          <Link to="/projects" className="block text-sm font-medium text-gray-600 no-underline py-2" onClick={() => setMobileOpen(false)}>Projects</Link>
          <hr className="border-gray-200" />
          {isAuthenticated ? (
            <>
              <Link to="/profile" className="block text-sm font-medium text-gray-700 no-underline py-2" onClick={() => setMobileOpen(false)}>Profile</Link>
              <button onClick={() => { logout(); setMobileOpen(false); }} className="w-full text-left text-sm font-medium text-gray-700 bg-gray-100 rounded-lg px-4 py-2 border-none cursor-pointer">Log out</button>
            </>
          ) : (
            <>
              <Link to="/login" className="block text-sm font-medium text-gray-700 no-underline py-2" onClick={() => setMobileOpen(false)}>Log in</Link>
              <Link to="/register" className="block text-center text-sm font-medium text-white bg-primary-600 rounded-lg px-4 py-2 no-underline" onClick={() => setMobileOpen(false)}>Sign up</Link>
            </>
          )}
        </div>
      )}
    </nav>
  );
}
