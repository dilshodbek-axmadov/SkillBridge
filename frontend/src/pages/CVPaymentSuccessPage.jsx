import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import api from '../services/api';
import { CheckCircle2, Loader2 } from 'lucide-react';

export default function CVPaymentSuccessPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const cvId = params.get('cv_id');
  const sessionId = params.get('session_id');

  const backTo = useMemo(() => {
    if (!cvId) return '/cv-builder';
    return `/cv-builder?cv_id=${encodeURIComponent(cvId)}`;
  }, [cvId]);

  const [seconds, setSeconds] = useState(5);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let mounted = true;
    let pollTimer = null;
    let countdownTimer = null;

    const verify = async () => {
      // Webhook-independent path: ask the backend to retrieve the Stripe
      // session, validate it, and persist the Payment row.
      if (!cvId || !sessionId) return false;
      try {
        const { data } = await api.post(
          `/cv/${cvId}/pay/verify/`,
          { session_id: sessionId }
        );
        if (mounted && data?.paid) {
          setReady(true);
          return true;
        }
      } catch {
        // fall through to polling — webhook may still come through
      }
      return false;
    };

    const poll = async () => {
      if (!cvId) return;
      try {
        const { data } = await api.get(`/cv/${cvId}/access-status/`);
        if (!mounted) return;
        if (data?.can_download) {
          setReady(true);
        }
      } catch {
        // ignore; webhook might not have updated yet
      }
    };

    // 1) Verify the session server-side (fast path, works without webhook).
    // 2) Fall back to polling access-status as a safety net.
    verify().then((ok) => {
      if (!mounted || ok) return;
      poll();
      pollTimer = setInterval(poll, 1000);
    });

    countdownTimer = setInterval(() => {
      setSeconds((s) => Math.max(0, s - 1));
    }, 1000);

    return () => {
      mounted = false;
      if (pollTimer) clearInterval(pollTimer);
      if (countdownTimer) clearInterval(countdownTimer);
    };
  }, [cvId, sessionId]);

  useEffect(() => {
    if (seconds <= 0) {
      navigate(backTo, { replace: true });
    }
  }, [seconds, navigate, backTo]);

  return (
    <div className="min-h-screen flex items-center justify-center px-4 bg-gray-50 dark:bg-gray-950">
      <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl shadow-sm max-w-lg w-full p-6 text-center">
        <div className="w-12 h-12 mx-auto rounded-xl bg-emerald-50 dark:bg-emerald-900/20 flex items-center justify-center mb-4">
          {ready ? (
            <CheckCircle2 className="w-6 h-6 text-emerald-600" />
          ) : (
            <Loader2 className="w-6 h-6 text-emerald-600 animate-spin" />
          )}
        </div>
        <h1 className="text-lg font-bold text-gray-900 dark:text-gray-100">
          Payment successful, preparing your CV download
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
          Redirecting back in {seconds}s…
        </p>
        <button
          onClick={() => navigate(backTo)}
          className="mt-5 inline-flex items-center justify-center px-4 py-2 rounded-lg bg-primary-600 text-white text-sm font-semibold hover:bg-primary-700 transition-colors border-none cursor-pointer"
        >
          Back to CV
        </button>
      </div>
    </div>
  );
}

