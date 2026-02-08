import { create } from 'zustand';
import api from '../services/api';

const useAuthStore = create((set) => ({
  user: null,
  isAuthenticated: !!localStorage.getItem('access_token'),
  loading: false,
  error: null,

  login: async (email, password) => {
    set({ loading: true, error: null });
    try {
      const { data } = await api.post('/users/auth/login/', { email, password });
      localStorage.setItem('access_token', data.tokens.access);
      localStorage.setItem('refresh_token', data.tokens.refresh);
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
      localStorage.setItem('access_token', data.tokens.access);
      localStorage.setItem('refresh_token', data.tokens.refresh);
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

  logout: async () => {
    try {
      const refresh = localStorage.getItem('refresh_token');
      if (refresh) {
        await api.post('/users/auth/logout/', { refresh_token: refresh });
      }
    } catch {
      // Ignore logout API errors
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      set({ user: null, isAuthenticated: false });
    }
  },

  fetchUser: async () => {
    if (!localStorage.getItem('access_token')) return;
    set({ loading: true });
    try {
      const { data } = await api.get('/users/auth/me/');
      set({ user: data.user, isAuthenticated: true, loading: false });
    } catch {
      set({ loading: false });
    }
  },

  clearError: () => set({ error: null }),
}));

export default useAuthStore;
