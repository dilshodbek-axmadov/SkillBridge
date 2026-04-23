import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { XCircle } from 'lucide-react';

export default function SubscriptionFailurePage() {
  const navigate = useNavigate();
  const [seconds, setSeconds] = useState(5);

  useEffect(() => {
    const t = setInterval(() => setSeconds((s) => Math.max(0, s - 1)), 1000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    if (seconds <= 0) navigate('/recruiter/analytics', { replace: true });
  }, [seconds, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center px-4 bg-gray-50 dark:bg-gray-950">
      <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl shadow-sm max-w-lg w-full p-6 text-center">
        <div className="w-12 h-12 mx-auto rounded-xl bg-red-50 dark:bg-red-900/20 flex items-center justify-center mb-4">
          <XCircle className="w-6 h-6 text-red-600" />
        </div>
        <h1 className="text-lg font-bold text-gray-900 dark:text-gray-100">Checkout cancelled</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
          No charge was made. You can try again whenever you&apos;re ready.
        </p>
        <p className="text-xs text-gray-400 mt-3">Redirecting in {seconds}s…</p>
        <button
          onClick={() => navigate('/recruiter/analytics', { replace: true })}
          className="mt-5 inline-flex items-center justify-center px-4 py-2 rounded-lg bg-primary-600 text-white text-sm font-semibold hover:bg-primary-700 transition-colors border-none cursor-pointer"
        >
          Back to recruiter
        </button>
      </div>
    </div>
  );
}
