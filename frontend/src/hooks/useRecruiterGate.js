import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import useAuthStore from '../store/authStore';

/**
 * Ensures only recruiter accounts stay on recruiter routes; loads user if needed.
 */
export default function useRecruiterGate() {
  const navigate = useNavigate();
  const { user, fetchUser } = useAuthStore();

  useEffect(() => {
    if (user?.user_type && user.user_type !== 'recruiter') {
      navigate('/dashboard', { replace: true });
    }
  }, [user, navigate]);

  useEffect(() => {
    if (!user && localStorage.getItem('access_token')) {
      fetchUser();
    }
  }, [user, fetchUser]);

  return { user, fetchUser };
}
