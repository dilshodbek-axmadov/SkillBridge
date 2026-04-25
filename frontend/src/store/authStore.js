import { create } from 'zustand';
import api from '../services/api';
import i18n from '../i18n';
import { safeGetItem, safeRemoveItem, safeSetItem } from '../utils/safeStorage';

const useAuthStore = create((set) => ({
  user: null,
  isAuthenticated: !!safeGetItem('access_token'),
  loading: false,
  error: null,

  login: async (email, password) => {
    set({ loading: true, error: null });
    try {
      const { data } = await api.post('/users/auth/login/', { email, password });
      safeSetItem('access_token', data.tokens.access);
      safeSetItem('refresh_token', data.tokens.refresh);
      if (data.user?.preferred_language) {
        i18n.changeLanguage(data.user.preferred_language);
      }
      set({ user: data.user, isAuthenticated: true, loading: false });
      return data;
    } catch (error) {
      const msg =
        error.response?.data?.non_field_errors?.[0] ||
        error.response?.data?.detail ||
        error.response?.data?.error ||
        'Invalid email or password';
      set({ error: msg, loading: false });
      throw error;
    }
  },

  register: async (userData) => {
    set({ loading: true, error: null });
    try {
      const { data } = await api.post('/users/auth/register/', userData);
      safeSetItem('access_token', data.tokens.access);
      safeSetItem('refresh_token', data.tokens.refresh);
      set({ user: data.user, isAuthenticated: true, loading: false });
      return data;
    } catch (error) {
      const errors = error.response?.data;
      let msg = 'Registration failed';
      if (errors) {
        if (typeof errors === 'string') {
          msg = errors;
        } else if (errors.detail) {
          msg = errors.detail;
        } else {
          // Collect first field error from Django serializer errors
          const firstKey = Object.keys(errors)[0];
          if (firstKey) {
            const val = errors[firstKey];
            msg = Array.isArray(val) ? val[0] : val;
          }
        }
      }
      set({ error: msg, loading: false });
      throw error;
    }
  },

  loginWithGoogle: async (accessToken, userType) => {
    set({ loading: true, error: null });
    try {
      const body = { access_token: accessToken };
      if (userType) body.user_type = userType;
      const { data } = await api.post('/users/auth/google/', body);
      safeSetItem('access_token', data.tokens.access);
      safeSetItem('refresh_token', data.tokens.refresh);
      if (data.user?.preferred_language) {
        i18n.changeLanguage(data.user.preferred_language);
      }
      set({ user: data.user, isAuthenticated: true, loading: false });
      return data;
    } catch (error) {
      const body = error.response?.data;
      const msg =
        body?.error ||
        body?.detail ||
        'Could not sign in with Google. Please try again.';
      set({ error: String(msg), loading: false });
      throw error;
    }
  },

  logout: async () => {
    try {
      const refresh = safeGetItem('refresh_token');
      if (refresh) {
        await api.post('/users/auth/logout/', { refresh_token: refresh });
      }
    } catch {
      // Ignore logout API errors
    } finally {
      safeRemoveItem('access_token');
      safeRemoveItem('refresh_token');
      set({ user: null, isAuthenticated: false });
    }
  },

  fetchUser: async () => {
    if (!safeGetItem('access_token')) return;
    set({ loading: true });
    try {
      const { data } = await api.get('/users/auth/me/');
      if (data.user?.preferred_language) {
        i18n.changeLanguage(data.user.preferred_language);
      }
      set({ user: data.user, isAuthenticated: true, loading: false });
    } catch {
      set({ loading: false });
    }
  },

  clearError: () => set({ error: null }),
}));

export default useAuthStore;
