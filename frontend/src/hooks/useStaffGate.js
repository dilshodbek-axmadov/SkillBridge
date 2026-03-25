import { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import useAuthStore from '../store/authStore';
import { safeGetItem } from '../utils/safeStorage';

function isStaffUser(user) {
  return !!(user?.is_staff || user?.is_superuser);
}

/**
 * Redirect non-staff away from in-app admin routes.
 */
export default function useStaffGate() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, fetchUser } = useAuthStore();

  useEffect(() => {
    if (!user && safeGetItem('access_token')) {
      fetchUser();
    }
  }, [user, fetchUser]);

  useEffect(() => {
    if (!safeGetItem('access_token')) {
      navigate(`/login?redirect=${encodeURIComponent(location.pathname)}`, { replace: true });
      return;
    }
    if (user != null && !isStaffUser(user)) {
      navigate('/dashboard', { replace: true });
    }
  }, [user, navigate, location.pathname]);

  return { user, fetchUser, isStaff: isStaffUser(user) };
}
