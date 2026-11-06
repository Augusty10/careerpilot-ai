import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { authAPI } from '../services/api';
import Input from '../components/Input';
import Button from '../components/Button';
import Alert from '../components/Alert';

export const Settings = () => {
  const { user, updateUser } = useAuth();

  // Name state
  const [name, setName] = useState(user?.name || '');
  const [nameLoading, setNameLoading] = useState(false);
  const [nameSuccess, setNameSuccess] = useState('');
  const [nameError, setNameError] = useState('');

  // Password state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [passwordSuccess, setPasswordSuccess] = useState('');
  const [passwordError, setPasswordError] = useState('');

  const handleUpdateName = async (e) => {
    e.preventDefault();
    if (!name.trim() || name.trim().length < 2) {
      setNameError('Name must be at least 2 characters');
      return;
    }

    setNameLoading(true);
    setNameSuccess('');
    setNameError('');

    try {
      const response = await authAPI.updateMe({ name: name.trim() });
      if (response.data && response.data.user) {
        updateUser(response.data.user);
        setNameSuccess('Name updated successfully!');
      }
    } catch (err) {
      setNameError(err.response?.data?.error || 'Failed to update name');
    } finally {
      setNameLoading(false);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setPasswordSuccess('');
    setPasswordError('');

    if (!currentPassword) {
      setPasswordError('Current password is required');
      return;
    }

    if (!newPassword) {
      setPasswordError('New password is required');
      return;
    } else if (newPassword.length < 8) {
      setPasswordError('New password must be at least 8 characters');
      return;
    } else if (!/[A-Za-z]/.test(newPassword)) {
      setPasswordError('New password must contain at least one letter');
      return;
    } else if (!/\d/.test(newPassword)) {
      setPasswordError('New password must contain at least one number');
      return;
    }

    if (newPassword !== confirmPassword) {
      setPasswordError('New passwords do not match');
      return;
    }

    setPasswordLoading(true);

    try {
      await authAPI.updateMe({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setPasswordSuccess('Password changed successfully!');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      setPasswordError(err.response?.data?.error || 'Failed to change password');
    } finally {
      setPasswordLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          Account Settings
        </h1>
        <p className="mt-1 text-sm text-slate-600">
          Manage your personal details and security preferences.
        </p>
      </div>

      <div className="space-y-8">
        {/* Profile Details Section */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8">
          <div className="flex items-center gap-2 mb-4 border-b border-slate-100 pb-3">
            <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
            <h2 className="text-lg font-bold text-slate-900">Profile Information</h2>
          </div>

          {nameSuccess && (
            <Alert type="success" message={nameSuccess} className="mb-4" onClose={() => setNameSuccess('')} />
          )}
          {nameError && (
            <Alert type="error" message={nameError} className="mb-4" onClose={() => setNameError('')} />
          )}

          <form onSubmit={handleUpdateName} className="space-y-4 max-w-md">
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1.5">
                Email Address
              </label>
              <input
                type="email"
                disabled
                value={user?.email || ''}
                className="w-full px-3.5 py-2.5 bg-slate-100 border border-slate-200 text-slate-500 rounded-lg text-sm cursor-not-allowed"
              />
              <p className="mt-1 text-xs text-slate-400">
                Your email address is your primary login identifier and cannot be modified.
              </p>
            </div>

            <Input
              id="name"
              name="name"
              label="Full Name"
              type="text"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                if (nameError) setNameError('');
              }}
              required
            />

            <div>
              <Button type="submit" variant="primary" loading={nameLoading}>
                Save Changes
              </Button>
            </div>
          </form>
        </div>

        {/* Change Password Section */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8">
          <div className="flex items-center gap-2 mb-4 border-b border-slate-100 pb-3">
            <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
            <h2 className="text-lg font-bold text-slate-900">Change Password</h2>
          </div>

          {passwordSuccess && (
            <Alert type="success" message={passwordSuccess} className="mb-4" onClose={() => setPasswordSuccess('')} />
          )}
          {passwordError && (
            <Alert type="error" message={passwordError} className="mb-4" onClose={() => setPasswordError('')} />
          )}

          <form onSubmit={handleChangePassword} className="space-y-4 max-w-md" noValidate>
            <Input
              id="currentPassword"
              name="currentPassword"
              label="Current Password"
              type="password"
              placeholder="Enter current password"
              value={currentPassword}
              onChange={(e) => {
                setCurrentPassword(e.target.value);
                if (passwordError) setPasswordError('');
              }}
              required
              autoComplete="current-password"
            />

            <Input
              id="newPassword"
              name="newPassword"
              label="New Password"
              type="password"
              placeholder="At least 8 chars with letter & number"
              value={newPassword}
              onChange={(e) => {
                setNewPassword(e.target.value);
                if (passwordError) setPasswordError('');
              }}
              helperText="Min. 8 characters with at least one letter and one number"
              required
              autoComplete="new-password"
            />

            <Input
              id="confirmNewPassword"
              name="confirmNewPassword"
              label="Confirm New Password"
              type="password"
              placeholder="Confirm new password"
              value={confirmPassword}
              onChange={(e) => {
                setConfirmPassword(e.target.value);
                if (passwordError) setPasswordError('');
              }}
              required
              autoComplete="new-password"
            />

            <div>
              <Button type="submit" variant="secondary" loading={passwordLoading}>
                Update Password
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Settings;

