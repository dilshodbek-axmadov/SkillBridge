import api from '../services/api';

/**
 * Kicks off the Recruiter Pro Stripe Checkout flow.
 *
 * Calls POST /recruiters/subscribe/, then redirects the current tab to the
 * Stripe-hosted checkout URL. On error, calls the optional onError callback
 * with a user-facing message.
 *
 * Returns true if the redirect was initiated, false on failure.
 */
export async function startProCheckout({ onError } = {}) {
  try {
    const { data } = await api.post('/recruiters/subscribe/');
    if (data?.checkout_url) {
      window.location.assign(data.checkout_url);
      return true;
    }
    onError?.('Stripe did not return a checkout URL. Please try again.');
    return false;
  } catch (e) {
    const body = e?.response?.data;
    if (body?.code === 'already_pro') {
      // Treat as success: just refresh to /recruiter/analytics so they see unlocked state.
      window.location.assign('/recruiter/analytics');
      return true;
    }
    const msg =
      body?.error ||
      body?.detail ||
      'Could not start checkout. Please try again in a moment.';
    onError?.(String(msg));
    return false;
  }
}
