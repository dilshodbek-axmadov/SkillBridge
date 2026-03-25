import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import useAuthStore from '../store/authStore';
import { safeGetItem } from '../utils/safeStorage';

/**
 * Ensures only recruiter accounts stay on recruiter routes; loads user if needed.
 */
export default function useRecruiterGate() {
  const navigate = useNavigate();
  const { user, fetchUser } = useAuthStore();

  useEffect(() => {
    const staff = user?.is_staff || user?.is_superuser;
    if (user?.user_type && user.user_type !== 'recruiter' && !staff) {
      navigate('/dashboard', { replace: true });
    }
  }, [user, navigate]);

  useEffect(() => {
    if (!user && safeGetItem('access_token')) {
      fetchUser();
    }
  }, [user, fetchUser]);

  return { user, fetchUser };
}
