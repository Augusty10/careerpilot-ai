import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { authAPI } from '../services/api';
import Input from '../components/Input';
import Button from '../components/Button';
import Alert from '../components/Alert';

export const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [serverMessage, setServerMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const validate = () => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email.trim() || !emailRegex.test(email.trim())) {
      setError('Please enter a valid email address');
      return false;
    }
    setError('');
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    setServerMessage('');

    try {
      const response = await authAPI.forgotPassword(email);
      setServerMessage(
        response.data.message ||
        'If an account with that email exists, a password reset link has been sent.'
      );
    } catch (err) {
      if (err.response?.status === 429) {
        setError('Too many requests. Please wait a minute before requesting another reset.');
      } else {
        // Fallback generic response to maintain security
        setServerMessage('If an account with that email exists, a password reset link has been sent.');
      }
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
            <span>Account Recovery</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Reset your password
          </h1>
          <p className="mt-2 text-sm text-slate-600">
            Enter your email and we'll generate a time-limited reset link.
          </p>
        </div>

        {/* Card */}
        <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200/80 shadow-xl shadow-slate-200/40">
          {serverMessage ? (
            <div className="space-y-5">
              <Alert type="success" message={serverMessage} />

              <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-800 space-y-1.5">
                <p className="font-semibold text-amber-900 flex items-center gap-1.5">
                  <svg className="w-4 h-4 shrink-0 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Console Output Notice (Module 1)
                </p>
                <p>
                  As configured for Module 1, the password reset link has been printed directly to your <strong>backend server console</strong> instead of sending an external email. Check your terminal logs to grab the link!
                </p>
              </div>

              <div className="pt-2 text-center">
                <Link
                  to="/login"
                  className="inline-flex items-center justify-center text-sm font-semibold text-indigo-600 hover:text-indigo-500 hover:underline"
                >
                  ← Back to Sign in
                </Link>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4" noValidate>
              {error && <Alert type="error" message={error} onClose={() => setError('')} />}

              <Input
                id="email"
                name="email"
                label="Registered Email Address"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  if (error) setError('');
                }}
                required
                autoComplete="email"
              />

              <div className="pt-2">
                <Button
                  type="submit"
                  variant="primary"
                  loading={loading}
                  className="w-full text-base py-3"
                >
                  Send Reset Link
                </Button>
              </div>

              <div className="pt-3 text-center">
                <Link
                  to="/login"
                  className="text-sm font-medium text-slate-600 hover:text-slate-900"
                >
                  Remember your password?{' '}
                  <span className="font-semibold text-indigo-600 hover:underline">
                    Sign in
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

export default ForgotPassword;

