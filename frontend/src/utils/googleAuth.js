/**
 * Google Identity Services (GIS) helper.
 *
 * Uses the OAuth 2.0 "token" flow with a custom button:
 *   getGoogleAccessToken() opens Google's hosted popup, returns an access_token.
 *
 * The access token is then POSTed to our backend, which verifies it against
 * Google's userinfo endpoint before issuing SkillBridge JWTs.
 *
 * Requires VITE_GOOGLE_CLIENT_ID to be set in frontend/.env.
 */

const GIS_SRC = 'https://accounts.google.com/gsi/client';

let scriptPromise = null;

function loadGoogleScript() {
  if (typeof window === 'undefined') {
    return Promise.reject(new Error('Google sign-in is only available in the browser.'));
  }
  if (window.google?.accounts?.oauth2) {
    return Promise.resolve();
  }
  if (scriptPromise) return scriptPromise;

  scriptPromise = new Promise((resolve, reject) => {
    const existing = document.querySelector(`script[src="${GIS_SRC}"]`);
    if (existing) {
      existing.addEventListener('load', () => resolve());
      existing.addEventListener('error', () => reject(new Error('Failed to load Google Identity Services.')));
      // If already loaded
      if (window.google?.accounts?.oauth2) resolve();
      return;
    }
    const s = document.createElement('script');
    s.src = GIS_SRC;
    s.async = true;
    s.defer = true;
    s.onload = () => resolve();
    s.onerror = () => {
      scriptPromise = null;
      reject(new Error('Failed to load Google Identity Services.'));
    };
    document.head.appendChild(s);
  });
  return scriptPromise;
}

export function isGoogleAuthConfigured() {
  return Boolean(import.meta.env.VITE_GOOGLE_CLIENT_ID);
}

/**
 * Opens Google's OAuth popup and resolves with an access_token string.
 * Rejects if the user closes the popup or the flow errors out.
 */
export async function getGoogleAccessToken() {
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
  if (!clientId) {
    throw new Error(
      'Google sign-in is not configured. Set VITE_GOOGLE_CLIENT_ID in frontend/.env.',
    );
  }

  await loadGoogleScript();

  return new Promise((resolve, reject) => {
    try {
      const tokenClient = window.google.accounts.oauth2.initTokenClient({
        client_id: clientId,
        scope: 'openid email profile',
        prompt: '',
        callback: (response) => {
          if (response?.error) {
            reject(new Error(response.error_description || response.error));
            return;
          }
          if (!response?.access_token) {
            reject(new Error('Google did not return an access token.'));
            return;
          }
          resolve(response.access_token);
        },
        error_callback: (err) => {
          const type = err?.type || 'unknown';
          if (type === 'popup_closed' || type === 'popup_failed_to_open') {
            reject(new Error('Google sign-in was closed before completing.'));
          } else {
            reject(new Error(err?.message || `Google sign-in error (${type}).`));
          }
        },
      });
      tokenClient.requestAccessToken({ prompt: '' });
    } catch (e) {
      reject(e);
    }
  });
}
