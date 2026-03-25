import { create } from 'zustand';
import { safeGetItem, safeSetItem } from '../utils/safeStorage';

const STORAGE_KEY = 'skillbridge-theme';

function getSystemPreference() {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function applyTheme(theme) {
  const resolved = theme === 'system' ? getSystemPreference() : theme;
  const root = document.documentElement;
  if (resolved === 'dark') {
    root.classList.add('dark');
  } else {
    root.classList.remove('dark');
  }
}

const useThemeStore = create((set, get) => ({
  theme: safeGetItem(STORAGE_KEY) || 'light',

  setTheme: (theme) => {
    safeSetItem(STORAGE_KEY, theme);
    applyTheme(theme);
    set({ theme });
  },

  initTheme: () => {
    const saved = safeGetItem(STORAGE_KEY) || 'light';
    applyTheme(saved);
    set({ theme: saved });

    // Listen for OS preference changes (relevant when theme is 'system')
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    mq.addEventListener('change', () => {
      if (get().theme === 'system') {
        applyTheme('system');
      }
    });
  },
}));

export default useThemeStore;
