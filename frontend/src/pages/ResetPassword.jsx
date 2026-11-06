import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { authAPI } from '../services/api';
import Input from '../components/Input';
import Button from '../components/Button';
import Alert from '../components/Alert';

export const ResetPassword = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const [token, setToken] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errors, setErrors] = useState({});
  const [serverError, setServerError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const tokenParam = params.get('token');
    if (tokenParam) {
      setToken(tokenParam);
    }
  }, [location]);

  const validate = () => {
    const errs = {};
    if (!token.trim()) {
      errs.token = 'Reset token is missing or invalid';
    }

    if (!password) {
      errs.password = 'New password is required';
    } else if (password.length < 8) {
      errs.password = 'Password must be at least 8 characters';
    } else if (!/[A-Za-z]/.test(password)) {
      errs.password = 'Password must contain at least one letter';
    } else if (!/\d/.test(password)) {
      errs.password = 'Password must contain at least one number';
    }

    if (password !== confirmPassword) {
      errs.confirmPassword = 'Passwords do not match';
    }

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    setServerError('');

    try {
      const response = await authAPI.resetPassword(token, password);
      setSuccessMessage(
        response.data.message ||
        'Password reset successful. You can now log in with your new password.'
      );
      // Wait 2.5s and redirect to login, or let user click button
      setTimeout(() => {
        navigate('/login?reset=true');
      }, 2500);
    } catch (err) {
      const msg = err.response?.data?.error || 'Invalid or expired reset token. Please request a new one.';
      setServerError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-700 text-xs font-semibold mb-3">
            <span>CareerPilot AI</span>
            <span>•</span>
            <span>Security</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Create new password
          </h1>
          <p className="mt-2 text-sm text-slate-600">
            Choose a strong password to protect your career profile.
          </p>
        </div>

        {/* Card */}
        <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200/80 shadow-xl shadow-slate-200/40">
          {successMessage ? (
            <div className="space-y-5">
              <Alert type="success" message={successMessage} />
              <Button
                variant="primary"
                onClick={() => navigate('/login?reset=true')}
                className="w-full py-3"
              >
                Go to Sign In
              </Button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4" noValidate>
              {serverError && (
                <Alert
                  type="error"
                  message={serverError}
                  className="mb-4"
                  onClose={() => setServerError('')}
                />
              )}

              {/* Show token field if not present in query string */}
              {!new URLSearchParams(location.search).get('token') && (
                <Input
                  id="token"
                  name="token"
                  label="Reset Token"
                  type="text"
                  placeholder="Paste token from console / email"
                  value={token}
                  onChange={(e) => {
                    setToken(e.target.value);
                    if (errors.token) setErrors((prev) => ({ ...prev, token: '' }));
                  }}
                  error={errors.token}
                  required
                />
              )}

              <Input
                id="password"
                name="password"
                label="New Password"
                type="password"
                placeholder="At least 8 characters with letter & number"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (errors.password) setErrors((prev) => ({ ...prev, password: '' }));
                }}
                error={errors.password}
                helperText="Min. 8 characters, at least 1 letter and 1 number"
                required
                autoComplete="new-password"
              />

              <Input
                id="confirmPassword"
                name="confirmPassword"
                label="Confirm New Password"
                type="password"
                placeholder="Re-enter your new password"
                value={confirmPassword}
                onChange={(e) => {
                  setConfirmPassword(e.target.value);
                  if (errors.confirmPassword) setErrors((prev) => ({ ...prev, confirmPassword: '' }));
                }}
                error={errors.confirmPassword}
                required
                autoComplete="new-password"
              />

              <div className="pt-2">
                <Button
                  type="submit"
                  variant="primary"
                  loading={loading}
                  className="w-full text-base py-3"
                >
                  Reset Password
                </Button>
              </div>

              <div className="pt-3 text-center">
                <Link
                  to="/login"
                  className="text-sm font-medium text-slate-600 hover:text-slate-900"
                >
                  Cancel and{' '}
                  <span className="font-semibold text-indigo-600 hover:underline">
                    return to sign in
                  </span>
                </Link>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default ResetPassword;

