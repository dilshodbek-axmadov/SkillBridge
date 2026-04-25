import { useMemo, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { Lock, Mail, Zap, Loader2, ArrowLeft } from 'lucide-react';
import api from '../services/api';

export default function ResetPasswordPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const email = useMemo(() => (searchParams.get('email') || '').trim(), [searchParams]);

  const [code, setCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [done, setDone] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (!email) {
      setError('Missing email. Please restart the password reset flow.');
      return;
    }
    if (!/^[0-9]{6}$/.test(code)) {
      setError('Code must be exactly 6 digits.');
      return;
    }
    if (newPassword !== confirm) {
      setError('Passwords do not match.');
      return;
    }
    setLoading(true);
    try {
      await api.post('/users/auth/password-reset-otp/confirm/', {
        email,
        code,
        new_password: newPassword,
        new_password_confirm: confirm,
      });
      setDone(true);
      setTimeout(() => navigate('/login'), 800);
    } catch (e2) {
      const body = e2?.response?.data;
      setError(body?.error || body?.detail || 'Could not reset password. Please try again.');
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
              to="/forgot-password"
              className="inline-flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300 no-underline hover:text-gray-900 dark:hover:text-white"
            >
              <ArrowLeft className="w-4 h-4" />
              Back
            </Link>
          </div>

          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-1">Reset your password</h1>
          <p className="text-gray-500 dark:text-gray-400 text-sm mb-6">
            Enter the 6-digit code sent to your email and choose a new password.
          </p>

          {email && (
            <div className="mb-5 p-3 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm text-gray-700 dark:text-gray-200 flex items-center gap-2">
              <Mail className="w-4 h-4 text-gray-500" />
              <span className="truncate">{email}</span>
            </div>
          )}

          {error && (
            <div className="mb-5 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 rounded-lg text-sm text-red-700">
              {error}
            </div>
          )}

          {done ? (
            <div className="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 rounded-lg text-sm text-green-700">
              Password updated. Redirecting to login…
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label htmlFor="code" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                  6-digit code
                </label>
                <input
                  id="code"
                  inputMode="numeric"
                  pattern="[0-9]{6}"
                  title="Enter a 6-digit code"
                  maxLength={6}
                  value={code}
                  onChange={(e) => setCode(e.target.value.replace(/\\D/g, '').slice(0, 6))}
                  placeholder="123456"
                  required
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-700 rounded-lg text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors bg-white dark:bg-gray-800 tracking-widest text-center"
                />
              </div>

              <div>
                <label htmlFor="new_password" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                  New password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500" />
                  <input
                    id="new_password"
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="Enter a new password"
                    required
                    className="w-full pl-11 pr-4 py-3 border border-gray-300 dark:border-gray-700 rounded-lg text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors bg-white dark:bg-gray-800"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="confirm" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                  Confirm password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500" />
                  <input
                    id="confirm"
                    type="password"
                    value={confirm}
                    onChange={(e) => setConfirm(e.target.value)}
                    placeholder="Confirm new password"
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
                {loading ? 'Updating…' : 'Update password'}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

