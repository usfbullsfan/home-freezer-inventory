import { useState, useEffect } from 'react';
import { settingsAPI, authAPI } from '../services/api';
import UserManagement from '../components/UserManagement';
import ImportExport from '../components/ImportExport';

function Settings({ user }) {
  const [settings, setSettings] = useState({
    track_history: 'true',
  });
  const [systemSettings, setSystemSettings] = useState({
    enable_image_fetching: 'true',
    no_auth_mode: 'false',
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [systemError, setSystemError] = useState('');
  const [systemSuccess, setSystemSuccess] = useState('');

  // Detect if running in development mode
  const isDev = import.meta.env.DEV;

  // Backup/Restore state
  const [backupInfo, setBackupInfo] = useState(null);
  const [backupLoading, setBackupLoading] = useState(false);
  const [backupError, setBackupError] = useState('');
  const [backupSuccess, setBackupSuccess] = useState('');
  const [restoreFile, setRestoreFile] = useState(null);

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
    if (user && user.role === 'admin') {
      loadBackupInfo();
      loadSystemSettings();
    }
  }, [user]);

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

  const loadSystemSettings = async () => {
    setSystemError('');

    try {
      const response = await settingsAPI.getSystemSettings();
      setSystemSettings(response.data);
    } catch (err) {
      setSystemError('Failed to load system settings');
    }
  };

  const handleSaveSystemSettings = async () => {
    setSystemError('');
    setSystemSuccess('');

    try {
      await settingsAPI.updateSystemSettings(systemSettings);
      setSystemSuccess('System settings saved successfully');
      setTimeout(() => setSystemSuccess(''), 3000);
    } catch (err) {
      setSystemError('Failed to save system settings');
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

  const loadBackupInfo = async () => {
    try {
      const response = await settingsAPI.getBackupInfo();
      setBackupInfo(response.data);
    } catch (err) {
      console.error('Failed to load backup info:', err);
    }
  };

  const handleDownloadBackup = async () => {
    setBackupError('');
    setBackupSuccess('');
    setBackupLoading(true);

    try {
      await settingsAPI.downloadBackup();
      setBackupSuccess('Backup downloaded successfully');
    } catch (err) {
      setBackupError(err.response?.data?.error || 'Failed to download backup');
    } finally {
      setBackupLoading(false);
    }
  };

  const handleRestoreBackup = async () => {
    if (!restoreFile) {
      setBackupError('Please select a backup file');
      return;
    }

    if (!window.confirm(
      'Are you sure you want to restore from this backup? This will replace your current database. A backup of your current database will be created automatically.'
    )) {
      return;
    }

    setBackupError('');
    setBackupSuccess('');
    setBackupLoading(true);

    try {
      const response = await settingsAPI.restoreBackup(restoreFile);
      setBackupSuccess(response.data.message);
      setRestoreFile(null);

      // Reload backup info after successful restore
      setTimeout(() => {
        loadBackupInfo();
      }, 1000);
    } catch (err) {
      setBackupError(err.response?.data?.error || 'Failed to restore backup');
    } finally {
      setBackupLoading(false);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (!file.name.endsWith('.db')) {
        setBackupError('Please select a valid .db file');
        setRestoreFile(null);
        return;
      }
      setRestoreFile(file);
      setBackupError('');
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
          <h3 style={{ marginBottom: '1.5rem' }}>System Settings (Admin)</h3>

          {systemError && <div className="error-message">{systemError}</div>}
          {systemSuccess && <div className="success-message">{systemSuccess}</div>}

          <div className="form-group" style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={systemSettings.enable_image_fetching === 'true'}
                onChange={(e) =>
                  setSystemSettings({
                    ...systemSettings,
                    enable_image_fetching: e.target.checked ? 'true' : 'false',
                  })
                }
                style={{ marginRight: '0.5rem', width: 'auto' }}
              />
              Enable automatic product image fetching
            </label>
            <small style={{ color: '#7f8c8d', marginLeft: '1.5rem', display: 'block', marginTop: '0.25rem' }}>
              When enabled, the system will automatically fetch product images from Pexels when adding items via UPC lookup. Disable this to conserve API quota or bandwidth.
            </small>
          </div>

          {isDev && (
            <div className="form-group" style={{ marginBottom: '1.5rem' }}>
              <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={systemSettings.no_auth_mode === 'true'}
                  onChange={(e) =>
                    setSystemSettings({
                      ...systemSettings,
                      no_auth_mode: e.target.checked ? 'true' : 'false',
                    })
                  }
                  style={{ marginRight: '0.5rem', width: 'auto' }}
                />
                Enable no-auth mode (Development Only)
              </label>
              <small style={{ color: '#7f8c8d', marginLeft: '1.5rem', display: 'block', marginTop: '0.25rem' }}>
                When enabled, quick login buttons will appear on the login page, allowing you to log in as any user without a password. This is only available in development mode.
              </small>
              <div
                style={{
                  background: '#fff3cd',
                  border: '1px solid #ffc107',
                  padding: '0.75rem',
                  borderRadius: '4px',
                  marginTop: '0.5rem',
                  marginLeft: '1.5rem',
                  fontSize: '0.875rem',
                }}
              >
                ⚠️ <strong>Security Warning:</strong> This feature is only for development environments. Never enable in production!
              </div>
            </div>
          )}

          <button
            className="btn btn-primary"
            onClick={handleSaveSystemSettings}
          >
            Save System Settings
          </button>
        </div>
      )}

      {user && user.role === 'admin' && (
        <UserManagement currentUser={user} />
      )}

      {user && user.role === 'admin' && (
        <div style={{ background: 'white', padding: '2rem', borderRadius: '8px', marginTop: '2rem' }}>
          <h3 style={{ marginBottom: '1.5rem' }}>Backup & Restore</h3>

          {backupError && <div className="error-message">{backupError}</div>}
          {backupSuccess && <div className="success-message">{backupSuccess}</div>}

          {backupInfo && (
            <div style={{
              background: '#f8f9fa',
              padding: '1rem',
              borderRadius: '4px',
              marginBottom: '1.5rem',
              border: '1px solid #e9ecef'
            }}>
              <h4 style={{ marginBottom: '0.75rem', fontSize: '1rem' }}>Current Database Information</h4>
              <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '0.5rem', fontSize: '0.9rem' }}>
                <strong>Size:</strong>
                <span>{backupInfo.file_size}</span>
                <strong>Last Modified:</strong>
                <span>{new Date(backupInfo.last_modified).toLocaleString()}</span>
                <strong>Total Items:</strong>
                <span>{backupInfo.total_items} ({backupInfo.active_items} active)</span>
                <strong>Categories:</strong>
                <span>{backupInfo.total_categories}</span>
                <strong>Users:</strong>
                <span>{backupInfo.total_users}</span>
              </div>
            </div>
          )}

          <div style={{ marginBottom: '2rem' }}>
            <h4 style={{ marginBottom: '0.5rem' }}>Download Backup</h4>
            <p style={{ color: '#7f8c8d', marginBottom: '1rem' }}>
              Download a complete backup of your freezer inventory database. Save this file in a safe location.
            </p>
            <button
              className="btn btn-primary"
              onClick={handleDownloadBackup}
              disabled={backupLoading}
            >
              {backupLoading ? 'Downloading...' : 'Download Backup'}
            </button>
          </div>

          <div>
            <h4 style={{ marginBottom: '0.5rem' }}>Restore from Backup</h4>
            <p style={{ color: '#7f8c8d', marginBottom: '1rem' }}>
              Upload a previously saved backup file to restore your database. Your current database will be backed up automatically before restoring.
            </p>
            <div style={{ marginBottom: '1rem' }}>
              <input
                type="file"
                accept=".db"
                onChange={handleFileSelect}
                style={{ marginBottom: '0.5rem' }}
              />
              {restoreFile && (
                <div style={{ color: '#27ae60', fontSize: '0.9rem' }}>
                  Selected: {restoreFile.name} ({(restoreFile.size / 1024).toFixed(2)} KB)
                </div>
              )}
            </div>
            <button
              className="btn btn-primary"
              onClick={handleRestoreBackup}
              disabled={backupLoading || !restoreFile}
            >
              {backupLoading ? 'Restoring...' : 'Restore Backup'}
            </button>
          </div>
        </div>
      )}

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
        <ImportExport />
      </div>

      <div style={{ background: 'white', padding: '2rem', borderRadius: '8px', marginTop: '2rem' }}>
        <h3 style={{ marginBottom: '1rem' }}>About</h3>
        <p style={{ color: '#7f8c8d' }}>
          <strong>Freezer Inventory Tracker</strong> - MVP Version
        </p>
        <p style={{ color: '#7f8c8d', marginTop: '0.5rem' }}>
          Track your freezer inventory with ease. Add items with simple codes and never lose track of what's in your freezer.
        </p>
      </div>
    </div>
  );
}

export default Settings;
