import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { XCircle } from 'lucide-react';

export default function CVPaymentFailurePage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const cvId = params.get('cv_id');

  const backTo = useMemo(() => {
    if (!cvId) return '/cv-builder';
    return `/cv-builder?cv_id=${encodeURIComponent(cvId)}`;
  }, [cvId]);

  const [seconds, setSeconds] = useState(5);

  useEffect(() => {
    const timer = setInterval(() => setSeconds((s) => Math.max(0, s - 1)), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    if (seconds <= 0) navigate(backTo, { replace: true });
  }, [seconds, navigate, backTo]);

  return (
    <div className="min-h-screen flex items-center justify-center px-4 bg-gray-50 dark:bg-gray-950">
      <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl shadow-sm max-w-lg w-full p-6 text-center">
        <div className="w-12 h-12 mx-auto rounded-xl bg-red-50 dark:bg-red-900/20 flex items-center justify-center mb-4">
          <XCircle className="w-6 h-6 text-red-600" />
        </div>
        <h1 className="text-lg font-bold text-gray-900 dark:text-gray-100">
          Payment failed or canceled
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
          Redirecting back in {seconds}s…
        </p>
        <button
          onClick={() => navigate(backTo)}
          className="mt-5 inline-flex items-center justify-center px-4 py-2 rounded-lg bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 text-sm font-semibold hover:opacity-90 transition-opacity border-none cursor-pointer"
        >
          Back to CV
        </button>
      </div>
    </div>
  );
}

