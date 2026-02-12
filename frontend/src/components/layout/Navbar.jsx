import { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Menu, X, Zap, ChevronDown } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import useAuthStore from '../../store/authStore';

/* ── Flag SVGs (crisp at any size) ── */
const FlagGB = () => (
  <svg viewBox="0 0 60 30" className="w-5 h-3.5 rounded-sm flex-shrink-0">
    <clipPath id="gb"><rect width="60" height="30" rx="2"/></clipPath>
    <g clipPath="url(#gb)">
      <rect width="60" height="30" fill="#012169"/>
      <path d="M0,0 L60,30 M60,0 L0,30" stroke="#fff" strokeWidth="6"/>
      <path d="M0,0 L60,30 M60,0 L0,30" stroke="#C8102E" strokeWidth="4" clipPath="url(#gb)"/>
      <path d="M30,0V30M0,15H60" stroke="#fff" strokeWidth="10"/>
      <path d="M30,0V30M0,15H60" stroke="#C8102E" strokeWidth="6"/>
    </g>
  </svg>
);

const FlagRU = () => (
  <svg viewBox="0 0 60 30" className="w-5 h-3.5 rounded-sm flex-shrink-0">
    <rect width="60" height="10" fill="#fff"/>
    <rect y="10" width="60" height="10" fill="#0039A6"/>
    <rect y="20" width="60" height="10" fill="#D52B1E"/>
  </svg>
);

const FlagUZ = () => (
  <svg viewBox="0 0 60 30" className="w-5 h-3.5 rounded-sm flex-shrink-0">
    <rect width="60" height="10" fill="#1EB53A"/>
    <rect y="10" width="60" height="1" fill="#CE1126"/>
    <rect y="0" width="60" height="10" fill="#0099B5"/>
    <rect y="11" width="60" height="1" fill="#CE1126"/>
    <rect y="12" width="60" height="18" fill="#1EB53A"/>
    <rect y="9" width="60" height="1" fill="#CE1126"/>
    <rect y="10" width="60" height="2" fill="#fff"/>
    <rect y="20" width="60" height="1" fill="#CE1126"/>
    <rect y="21" width="60" height="9" fill="#fff"/>
    <circle cx="10" cy="4.5" r="3.5" fill="#fff"/>
    <circle cx="11.5" cy="4.5" r="3.5" fill="#0099B5"/>
  </svg>
);

const LANGUAGES = [
  { code: 'en', label: 'English', shortLabel: 'EN', Flag: FlagGB },
  { code: 'ru', label: 'Русский', shortLabel: 'RU', Flag: FlagRU },
  { code: 'uz', label: "O'zbekcha", shortLabel: 'UZ', Flag: FlagUZ },
];

/* ── Language Switcher ── */
function LanguageSwitcher({ compact = false }) {
  const { i18n } = useTranslation();
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  const current = LANGUAGES.find((l) => l.code === i18n.language) || LANGUAGES[0];

  useEffect(() => {
    const close = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', close);
    return () => document.removeEventListener('mousedown', close);
  }, []);

  const handleChange = (code) => {
    i18n.changeLanguage(code);
    setOpen(false);
  };

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 text-sm font-medium text-gray-700 dark:text-gray-300 cursor-pointer transition-colors"
      >
        <current.Flag />
        <span>{compact ? current.shortLabel : current.label}</span>
        <ChevronDown className={`w-3.5 h-3.5 text-gray-400 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div className="absolute right-0 mt-1 w-44 bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 shadow-lg py-1 z-50">
          {LANGUAGES.map((lang) => (
            <button
              key={lang.code}
              onClick={() => handleChange(lang.code)}
              className={`w-full flex items-center gap-2.5 px-3 py-2 text-sm text-left cursor-pointer border-none transition-colors ${
                lang.code === current.code
                  ? 'bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400 font-semibold'
                  : 'bg-transparent text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
              }`}
            >
              <lang.Flag />
              {lang.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

/* ── Mobile Language Buttons ── */
function MobileLanguageSwitcher() {
  const { i18n } = useTranslation();
  return (
    <div className="flex gap-2">
      {LANGUAGES.map((lang) => (
        <button
          key={lang.code}
          onClick={() => i18n.changeLanguage(lang.code)}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border cursor-pointer transition-colors ${
            i18n.language === lang.code
              ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400'
              : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:border-gray-300 dark:hover:border-gray-600'
          }`}
        >
          <lang.Flag />
          {lang.shortLabel}
        </button>
      ))}
    </div>
  );
}

/* ── Main Navbar ── */
export default function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const { isAuthenticated, logout } = useAuthStore();
  const { t } = useTranslation();

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 dark:bg-gray-900/90 backdrop-blur-md border-b border-gray-200 dark:border-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 no-underline">
            <div className="w-8 h-8 bg-gradient-to-br from-primary-600 to-purple-500 rounded-lg flex items-center justify-center">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-gray-900 dark:text-gray-100">
              Skill<span className="text-primary-600 dark:text-primary-400">Bridge</span>
            </span>
          </Link>

          {/* Desktop nav */}
          <div className="hidden md:flex items-center gap-8">
            <Link to="/" className="text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 no-underline transition-colors">
              {t('nav.home')}
            </Link>
            <Link to="/dashboard" className="text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 no-underline transition-colors">
              {t('nav.dashboard')}
            </Link>
            <Link to="/roadmap" className="text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 no-underline transition-colors">
              {t('nav.roadmap')}
            </Link>
            <Link to="/projects" className="text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 no-underline transition-colors">
              {t('nav.projects')}
            </Link>
          </div>

          {/* Language + Auth buttons */}
          <div className="hidden md:flex items-center gap-3">
            <LanguageSwitcher />

            {isAuthenticated ? (
              <>
                <Link
                  to="/profile"
                  className="text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 no-underline transition-colors"
                >
                  {t('nav.profile')}
                </Link>
                <button
                  onClick={logout}
                  className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors cursor-pointer border-none"
                >
                  {t('nav.logout')}
                </button>
              </>
            ) : (
              <>
                <Link
                  to="/login"
                  className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 no-underline transition-colors"
                >
                  {t('nav.login')}
                </Link>
                <Link
                  to="/register"
                  className="px-5 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 no-underline transition-colors"
                >
                  {t('nav.signup')}
                </Link>
              </>
            )}
          </div>

          {/* Mobile toggle */}
          <button
            className="md:hidden p-2 text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white bg-transparent border-none cursor-pointer"
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800 px-4 py-4 space-y-3">
          <MobileLanguageSwitcher />
          <hr className="border-gray-200 dark:border-gray-800" />
          <Link to="/" className="block text-sm font-medium text-gray-600 dark:text-gray-300 no-underline py-2" onClick={() => setMobileOpen(false)}>{t('nav.home')}</Link>
          <Link to="/dashboard" className="block text-sm font-medium text-gray-600 dark:text-gray-300 no-underline py-2" onClick={() => setMobileOpen(false)}>{t('nav.dashboard')}</Link>
          <Link to="/roadmap" className="block text-sm font-medium text-gray-600 dark:text-gray-300 no-underline py-2" onClick={() => setMobileOpen(false)}>{t('nav.roadmap')}</Link>
          <Link to="/projects" className="block text-sm font-medium text-gray-600 dark:text-gray-300 no-underline py-2" onClick={() => setMobileOpen(false)}>{t('nav.projects')}</Link>
          <hr className="border-gray-200 dark:border-gray-800" />
          {isAuthenticated ? (
            <>
              <Link to="/profile" className="block text-sm font-medium text-gray-700 dark:text-gray-300 no-underline py-2" onClick={() => setMobileOpen(false)}>{t('nav.profile')}</Link>
              <button onClick={() => { logout(); setMobileOpen(false); }} className="w-full text-left text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 rounded-lg px-4 py-2 border-none cursor-pointer">{t('nav.logout')}</button>
            </>
          ) : (
            <>
              <Link to="/login" className="block text-sm font-medium text-gray-700 dark:text-gray-300 no-underline py-2" onClick={() => setMobileOpen(false)}>{t('nav.login')}</Link>
              <Link to="/register" className="block text-center text-sm font-medium text-white bg-primary-600 rounded-lg px-4 py-2 no-underline" onClick={() => setMobileOpen(false)}>{t('nav.signup')}</Link>
            </>
          )}
        </div>
      )}
    </nav>
  );
}
