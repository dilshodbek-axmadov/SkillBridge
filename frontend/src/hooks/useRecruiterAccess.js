import { useCallback, useEffect, useState } from 'react';
import api from '../services/api';

/**
 * Fetches recruiter plan/access state from the backend (source of truth).
 *
 * Returned shape mirrors apps.payments.recruiter_access.get_recruiter_access_state:
 *   {
 *     plan: 'free' | 'pro',
 *     is_pro: boolean,
 *     jobs: { allowed, used, limit, remaining, reason, code, window_days, plan },
 *     analytics: { allowed, reason, code, plan },
 *     developer_visibility_limit: number | null,
 *     upgrade_required: boolean,
 *   }
 *
 * The `refresh` function re-fetches — call after Stripe redirects / window focus.
 */
export default function useRecruiterAccess() {
  const [access, setAccess] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await api.get('/recruiters/access/');
      setAccess(data);
      setError(null);
    } catch (e) {
      setError(e?.response?.data?.error || e.message);
      setAccess(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    const onFocus = () => refresh();
    window.addEventListener('focus', onFocus);
    return () => window.removeEventListener('focus', onFocus);
  }, [refresh]);

  return { access, loading, error, refresh };
}
