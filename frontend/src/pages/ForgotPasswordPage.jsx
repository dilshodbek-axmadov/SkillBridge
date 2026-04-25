import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, Zap, Loader2, ArrowLeft } from 'lucide-react';
import api from '../services/api';

export default function ForgotPasswordPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await api.post('/users/auth/password-reset-otp/', { email });
      navigate(`/reset-password?email=${encodeURIComponent(email)}`);
    } catch (e2) {
      const body = e2?.response?.data;
      setError(body?.error || body?.detail || 'Could not send reset code. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-gray-50 dark:bg-gray-950">
      <div className="w-full max-w-md">
        <div className="flex items-center gap-2 mb-8 justify-center">
          <div className="w-9 h-9 bg-gradient-to-br from-primary-600 to-purple-500 rounded-lg flex items-center justify-center">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <span className="text-xl font-bold text-gray-900 dark:text-gray-100">
            Skill<span className="text-primary-600">Bridge</span>
          </span>
        </div>

        <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-800 p-8">
          <div className="flex items-center gap-2 mb-2">
            <Link
              to="/login"
              className="inline-flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300 no-underline hover:text-gray-900 dark:hover:text-white"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to login
            </Link>
          </div>

          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-1">Forgot password?</h1>
          <p className="text-gray-500 dark:text-gray-400 text-sm mb-6">
            Enter your email and we&apos;ll send you a 6-digit code.
          </p>

          {error && (
            <div className="mb-5 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 rounded-lg text-sm text-red-700">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                Email address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500" />
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  required
                  className="w-full pl-11 pr-4 py-3 border border-gray-300 dark:border-gray-700 rounded-lg text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors bg-white dark:bg-gray-800"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full h-[44px] bg-primary-600 hover:bg-primary-700 disabled:bg-primary-400 text-white text-sm font-semibold rounded-lg transition-colors cursor-pointer border-none flex items-center justify-center gap-2"
            >
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : null}
              {loading ? 'Sending code…' : 'Send reset code'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

