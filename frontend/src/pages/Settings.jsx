import { useState, useEffect } from 'react';
import { settingsAPI, authAPI } from '../services/api';

function Settings({ user }) {
  const [settings, setSettings] = useState({
    track_history: 'true',
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Password change state
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });
  const [passwordError, setPasswordError] = useState('');
  const [passwordSuccess, setPasswordSuccess] = useState('');

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await settingsAPI.getSettings();
      setSettings(response.data);
    } catch (err) {
      setError('Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveSettings = async () => {
    setError('');
    setSuccess('');

    try {
      await settingsAPI.updateSettings(settings);
      setSuccess('Settings saved successfully');
    } catch (err) {
      setError('Failed to save settings');
    }
  };

  const handlePurgeHistory = async () => {
    if (!window.confirm(
      'Are you sure you want to permanently delete all consumed and thrown out items? This cannot be undone.'
    )) {
      return;
    }

    setError('');
    setSuccess('');

    try {
      const response = await settingsAPI.purgeHistory();
      setSuccess(response.data.message);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to purge history');
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setPasswordError('');
    setPasswordSuccess('');

    // Validate passwords match
    if (passwordData.new_password !== passwordData.confirm_password) {
      setPasswordError('New passwords do not match');
      return;
    }

    // Validate password length
    if (passwordData.new_password.length < 6) {
      setPasswordError('Password must be at least 6 characters');
      return;
    }

    try {
      await authAPI.changePassword(passwordData.current_password, passwordData.new_password);
      setPasswordSuccess('Password changed successfully');
      setPasswordData({
        current_password: '',
        new_password: '',
        confirm_password: '',
      });
    } catch (err) {
      setPasswordError(err.response?.data?.error || 'Failed to change password');
    }
  };

  if (loading) {
    return (
      <div className="container">
        <div className="loading">Loading settings...</div>
      </div>
    );
  }

  return (
    <div className="container">
      <h2>Settings</h2>

      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}

      <div style={{ background: 'white', padding: '2rem', borderRadius: '8px', marginTop: '2rem' }}>
        <h3 style={{ marginBottom: '1.5rem' }}>General Settings</h3>

        <div className="form-group">
          <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={settings.track_history === 'true'}
              onChange={(e) =>
                setSettings({
                  ...settings,
                  track_history: e.target.checked ? 'true' : 'false',
                })
              }
              style={{ marginRight: '0.5rem', width: 'auto' }}
            />
            Track history of consumed and discarded items
          </label>
          <small style={{ color: '#7f8c8d', marginLeft: '1.5rem', display: 'block', marginTop: '0.25rem' }}>
            When enabled, items marked as consumed or thrown out will be kept in the database for historical tracking
          </small>
        </div>

        <button
          className="btn btn-primary"
          onClick={handleSaveSettings}
          style={{ marginTop: '1.5rem' }}
        >
          Save Settings
        </button>
      </div>

      <div style={{ background: 'white', padding: '2rem', borderRadius: '8px', marginTop: '2rem' }}>
        <h3 style={{ marginBottom: '1.5rem' }}>Change Password</h3>

        {passwordError && <div className="error-message">{passwordError}</div>}
        {passwordSuccess && <div className="success-message">{passwordSuccess}</div>}

        <form onSubmit={handleChangePassword}>
          <div className="form-group">
            <label htmlFor="current_password">Current Password</label>
            <input
              type="password"
              id="current_password"
              value={passwordData.current_password}
              onChange={(e) => setPasswordData({ ...passwordData, current_password: e.target.value })}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="new_password">New Password</label>
            <input
              type="password"
              id="new_password"
              value={passwordData.new_password}
              onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
              required
              minLength="6"
            />
            <small style={{ color: '#7f8c8d', display: 'block', marginTop: '0.25rem' }}>
              Must be at least 6 characters
            </small>
          </div>

          <div className="form-group">
            <label htmlFor="confirm_password">Confirm New Password</label>
            <input
              type="password"
              id="confirm_password"
              value={passwordData.confirm_password}
              onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
              required
              minLength="6"
            />
          </div>

          <button type="submit" className="btn btn-primary">
            Change Password
          </button>
        </form>
      </div>

      {user && user.role === 'admin' && (
        <div style={{ background: 'white', padding: '2rem', borderRadius: '8px', marginTop: '2rem' }}>
          <h3 style={{ marginBottom: '1rem', color: '#e74c3c' }}>Danger Zone</h3>

          <div style={{ marginBottom: '1rem' }}>
            <h4 style={{ marginBottom: '0.5rem' }}>Purge History</h4>
            <p style={{ color: '#7f8c8d', marginBottom: '1rem' }}>
              Permanently delete all consumed and thrown out items from the database. This action cannot be undone.
            </p>
            <button className="btn btn-danger" onClick={handlePurgeHistory}>
              Purge All History
            </button>
          </div>
        </div>
      )}

      <div style={{ background: 'white', padding: '2rem', borderRadius: '8px', marginTop: '2rem' }}>
        <h3 style={{ marginBottom: '1rem' }}>About</h3>
        <p style={{ color: '#7f8c8d' }}>
          <strong>Freezer Inventory Tracker</strong> - MVP Version
        </p>
        <p style={{ color: '#7f8c8d', marginTop: '0.5rem' }}>
          Track your freezer inventory with ease. Add items, scan QR codes, and never lose track of what's in your freezer.
        </p>
      </div>
    </div>
  );
}

export default Settings;
