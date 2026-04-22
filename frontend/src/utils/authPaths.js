/**
 * Post-auth landing path from API user shape (`user_type`: developer | recruiter).
 */
export function getHomePathForUser(user) {
  if (!user) return '/dashboard';
  if (user.user_type === 'recruiter') return '/recruiter/dashboard';
  // Developers must complete profile first (CV upload or manual form).
  return user.profile_completed ? '/dashboard' : '/profile-setup';
}
