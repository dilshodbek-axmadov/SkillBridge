/**
 * Post-auth landing path from API user shape (`user_type`: developer | recruiter).
 */
export function getHomePathForUser(user) {
  if (!user) return '/dashboard';
  return user.user_type === 'recruiter' ? '/recruiter/dashboard' : '/dashboard';
}
