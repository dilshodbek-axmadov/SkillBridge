import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { CheckCircle2, Loader2 } from 'lucide-react';
import api from '../services/api';

/**
 * Landing page after Stripe Checkout (subscription mode) success.
 *
 * Strategy: call /recruiters/subscribe/verify/ with the Stripe session_id
 * immediately — that endpoint verifies with Stripe and syncs Subscription +
 * flips User.recruiter_plan server-side (webhook-independent). Then poll
 * /recruiters/access/ as a belt-and-suspenders check, and redirect.
 */
export default function SubscriptionSuccessPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const sessionId = params.get('session_id');
  const [seconds, setSeconds] = useState(6);
  const [isPro, setIsPro] = useState(false);
  const [verifyError, setVerifyError] = useState('');

  useEffect(() => {
    let mounted = true;
    let pollTimer = null;
    let countdownTimer = null;

    const verify = async () => {
      if (!sessionId) return;
      try {
        const { data } = await api.post('/recruiters/subscribe/verify/', {
          session_id: sessionId,
        });
        if (!mounted) return;
        if (data?.is_pro) setIsPro(true);
      } catch (e) {
        if (!mounted) return;
        const msg = e?.response?.data?.error || e.message || 'Could not verify subscription.';
        setVerifyError(String(msg));
      }
    };

    const poll = async () => {
      try {
        const { data } = await api.get('/recruiters/access/');
        if (!mounted) return;
        if (data?.is_pro) setIsPro(true);
      } catch {
        /* ignore; webhook may still be propagating */
      }
    };

    verify();
    poll();
    pollTimer = setInterval(poll, 1500);
    countdownTimer = setInterval(() => setSeconds((s) => Math.max(0, s - 1)), 1000);

    return () => {
      mounted = false;
      if (pollTimer) clearInterval(pollTimer);
      if (countdownTimer) clearInterval(countdownTimer);
    };
  }, [sessionId]);

  useEffect(() => {
    if (seconds <= 0) {
      navigate('/recruiter/analytics', { replace: true });
    }
  }, [seconds, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center px-4 bg-gray-50 dark:bg-gray-950">
      <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl shadow-sm max-w-lg w-full p-6 text-center">
        <div className="w-12 h-12 mx-auto rounded-xl bg-emerald-50 dark:bg-emerald-900/20 flex items-center justify-center mb-4">
          {isPro ? (
            <CheckCircle2 className="w-6 h-6 text-emerald-600" />
          ) : (
            <Loader2 className="w-6 h-6 text-emerald-600 animate-spin" />
          )}
        </div>
        <h1 className="text-lg font-bold text-gray-900 dark:text-gray-100">
          {isPro ? 'Welcome to Recruiter Pro' : 'Payment successful, activating your plan…'}
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
          {isPro
            ? 'Unlimited job posts, full candidate results, and analytics are now unlocked.'
            : 'Hold on, we are confirming your subscription with Stripe.'}
        </p>
        {verifyError && !isPro && (
          <p className="mt-3 text-xs text-red-600 dark:text-red-400">{verifyError}</p>
        )}
        <p className="text-xs text-gray-400 mt-3">Redirecting in {seconds}s…</p>
        <button
          onClick={() => navigate('/recruiter/analytics', { replace: true })}
          className="mt-5 inline-flex items-center justify-center px-4 py-2 rounded-lg bg-primary-600 text-white text-sm font-semibold hover:bg-primary-700 transition-colors border-none cursor-pointer"
        >
          Go to analytics
        </button>
      </div>
    </div>
  );
}
