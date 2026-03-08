import { useState, useEffect } from 'react';
import { notificationsAPI, itemsAPI } from '../services/api';
import Autocomplete from '../components/Autocomplete';

function EmailNotifications() {
  // ── Email address state ────────────────────────────────────────────────────
  const [emailConfigured, setEmailConfigured] = useState(false);
  const [myEmail, setMyEmail] = useState('');
  const [myEmailVerified, setMyEmailVerified] = useState(false);
  const [emailInput, setEmailInput] = useState('');
  const [emailError, setEmailError] = useState('');
  const [emailSuccess, setEmailSuccess] = useState('');
  const [emailLoading, setEmailLoading] = useState(false);

  const [verificationCode, setVerificationCode] = useState('');
  const [verifyError, setVerifyError] = useState('');
  const [verifySuccess, setVerifySuccess] = useState('');
  const [verifyLoading, setVerifyLoading] = useState(false);

  const [testEmailError, setTestEmailError] = useState('');
  const [testEmailSuccess, setTestEmailSuccess] = useState('');
  const [testEmailLoading, setTestEmailLoading] = useState(false);

  // ── Low-stock alerts state ─────────────────────────────────────────────────
  const [alerts, setAlerts] = useState([]);
  const [alertsLoading, setAlertsLoading] = useState(true);
  const [alertsError, setAlertsError] = useState('');

  // Add-alert form
  const [newItemName, setNewItemName] = useState('');
  const [newThreshold, setNewThreshold] = useState(2);
  const [addError, setAddError] = useState('');
  const [addLoading, setAddLoading] = useState(false);

  // Names available in the freezer for the restricted typeahead
  const [itemNameSuggestions, setItemNameSuggestions] = useState([]);

  // ── Load on mount ──────────────────────────────────────────────────────────
  useEffect(() => {
    const load = async () => {
      try {
        const [statusRes, emailRes] = await Promise.all([
          notificationsAPI.getStatus(),
          notificationsAPI.getMyEmail(),
        ]);
        setEmailConfigured(statusRes.data.configured);
        setMyEmail(emailRes.data.email || '');
        setEmailInput(emailRes.data.email || '');
        setMyEmailVerified(emailRes.data.email_verified || false);
      } catch {
        // non-critical
      }

      try {
        const res = await notificationsAPI.getLowStockAlerts();
        setAlerts(res.data);
      } catch (err) {
        console.error('getLowStockAlerts failed:', err?.response?.status, err?.response?.data, err?.message);
        setAlertsError('Failed to load alerts.');
      } finally {
        setAlertsLoading(false);
      }

      try {
        const namesRes = await itemsAPI.getItemNames('in_freezer');
        setItemNameSuggestions(namesRes.data.names || []);
      } catch (err) {
        console.error('getItemNames failed:', err?.response?.status, err?.response?.data, err?.message);
      }
    };
    load();
  }, []);

  // ── Email address handlers ─────────────────────────────────────────────────
  const handleSaveEmail = async () => {
    setEmailError('');
    setEmailSuccess('');
    setEmailLoading(true);
    try {
      const res = await notificationsAPI.updateMyEmail(emailInput.trim());
      setMyEmail(res.data.email || '');
      setMyEmailVerified(res.data.email_verified || false);
      setVerificationCode('');
      setVerifyError('');
      setVerifySuccess('');
      if (res.data.verification_required) {
        setEmailSuccess(`Verification code sent to ${res.data.email}`);
      } else if (!res.data.email) {
        setEmailSuccess('Email removed.');
      } else {
        setEmailSuccess('Email already verified.');
      }
    } catch (err) {
      setEmailError(err.response?.data?.error || 'Failed to save email.');
    } finally {
      setEmailLoading(false);
    }
  };

  const handleVerifyCode = async () => {
    setVerifyError('');
    setVerifySuccess('');
    setVerifyLoading(true);
    try {
      await notificationsAPI.verifyEmail(verificationCode.trim());
      setMyEmailVerified(true);
      setVerifySuccess('Email verified!');
      setVerificationCode('');
    } catch (err) {
      setVerifyError(err.response?.data?.error || 'Verification failed.');
    } finally {
      setVerifyLoading(false);
    }
  };

  const handleResendCode = async () => {
    setVerifyError('');
    setVerifySuccess('');
    try {
      await notificationsAPI.resendVerification();
      setVerifySuccess(`New code sent to ${myEmail}`);
    } catch (err) {
      setVerifyError(err.response?.data?.error || 'Failed to resend code.');
    }
  };

  const handleSendTestEmail = async () => {
    setTestEmailError('');
    setTestEmailSuccess('');
    setTestEmailLoading(true);
    try {
      const res = await notificationsAPI.sendTestEmail();
      setTestEmailSuccess(res.data.message || 'Test email sent!');
    } catch (err) {
      setTestEmailError(err.response?.data?.error || 'Failed to send test email.');
    } finally {
      setTestEmailLoading(false);
    }
  };

  // ── Low-stock alert handlers ───────────────────────────────────────────────
  const handleAddAlert = async () => {
    setAddError('');
    const name = newItemName.trim();
    if (!name) { setAddError('Item name is required.'); return; }
    if (!Number.isInteger(Number(newThreshold)) || Number(newThreshold) < 1) {
      setAddError('Threshold must be a positive number.'); return;
    }
    setAddLoading(true);
    try {
      const res = await notificationsAPI.createLowStockAlert(name, Number(newThreshold));
      setAlerts(prev => [...prev, res.data].sort((a, b) => a.item_name.localeCompare(b.item_name)));
      setNewItemName('');
      setNewThreshold(2);
    } catch (err) {
      setAddError(err.response?.data?.error || 'Failed to create alert.');
    } finally {
      setAddLoading(false);
    }
  };

  const handleToggleEnabled = async (alert) => {
    try {
      const res = await notificationsAPI.updateLowStockAlert(alert.id, { enabled: !alert.enabled });
      setAlerts(prev => prev.map(a => a.id === alert.id ? res.data : a));
    } catch {
      setAlertsError('Failed to update alert.');
    }
  };

  const handleThresholdChange = async (alert, value) => {
    const threshold = parseInt(value, 10);
    if (!threshold || threshold < 1) return;
    try {
      const res = await notificationsAPI.updateLowStockAlert(alert.id, { threshold });
      setAlerts(prev => prev.map(a => a.id === alert.id ? res.data : a));
    } catch {
      setAlertsError('Failed to update threshold.');
    }
  };

  const handleDeleteAlert = async (id) => {
    try {
      await notificationsAPI.deleteLowStockAlert(id);
      setAlerts(prev => prev.filter(a => a.id !== id));
    } catch {
      setAlertsError('Failed to delete alert.');
    }
  };

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="page-container" style={{ maxWidth: '700px', margin: '0 auto', padding: '2rem 1rem' }}>
      <h2 style={{ margin: '0 0 0.25rem' }}>Email Notifications</h2>
      <p style={{ color: '#6c757d', margin: '0 0 2rem', fontSize: '0.95rem' }}>
        Manage your notification email address and low-stock alerts.
      </p>

      {/* ── Email address section ────────────────────────────────────────── */}
      <section style={sectionStyle}>
        <h3 style={sectionHeadingStyle}>Notification email address</h3>

        {!emailConfigured && (
          <div style={warningBannerStyle}>
            Email notifications are not configured on this server. Contact your administrator.
          </div>
        )}

        {emailError && <div className="error-message" style={{ marginBottom: '0.75rem' }}>{emailError}</div>}
        {emailSuccess && <div className="success-message" style={{ marginBottom: '0.75rem' }}>{emailSuccess}</div>}

        <p style={{ margin: '0 0 0.75rem', fontSize: '0.875rem', color: '#7f8c8d' }}>
          Notifications will be sent to this address. It must be verified before alerts fire.
        </p>

        {myEmail && (
          <div style={{ marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '0.9rem', color: '#495057' }}>{myEmail}</span>
            {myEmailVerified ? (
              <span style={verifiedBadgeStyle}>Verified</span>
            ) : (
              <span style={unverifiedBadgeStyle}>Not verified</span>
            )}
          </div>
        )}

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <input
            type="email"
            value={emailInput}
            onChange={(e) => setEmailInput(e.target.value)}
            placeholder="you@example.com"
            style={{ flex: 1 }}
            disabled={!emailConfigured}
          />
          <button className="btn btn-primary" onClick={handleSaveEmail} disabled={emailLoading || !emailConfigured}>
            {emailLoading ? 'Saving…' : 'Save'}
          </button>
          {myEmail && (
            <button
              className="btn btn-secondary"
              onClick={() => setEmailInput('')}
              disabled={emailLoading || !emailConfigured}
            >
              Clear
            </button>
          )}
        </div>

        {/* Verification code entry */}
        {myEmail && !myEmailVerified && (
          <div style={{ marginTop: '1.25rem', padding: '1rem', background: '#f8f9fa', border: '1px solid #e9ecef', borderRadius: '6px' }}>
            <h4 style={{ margin: '0 0 0.75rem', fontSize: '0.95rem' }}>Verify your email</h4>
            <p style={{ margin: '0 0 0.75rem', fontSize: '0.875rem', color: '#7f8c8d' }}>
              Enter the 6-digit code sent to <strong>{myEmail}</strong>.
            </p>
            {verifyError && <div className="error-message" style={{ marginBottom: '0.75rem' }}>{verifyError}</div>}
            {verifySuccess && <div className="success-message" style={{ marginBottom: '0.75rem' }}>{verifySuccess}</div>}
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
              <input
                type="text"
                value={verificationCode}
                onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                placeholder="123456"
                maxLength={6}
                style={{ width: '8rem', fontFamily: 'monospace', fontSize: '1.25rem', letterSpacing: '0.2em', textAlign: 'center' }}
              />
              <button className="btn btn-primary" onClick={handleVerifyCode} disabled={verifyLoading || verificationCode.length !== 6}>
                {verifyLoading ? 'Verifying…' : 'Verify'}
              </button>
              <button className="btn btn-secondary" onClick={handleResendCode} style={{ fontSize: '0.85rem' }}>
                Resend code
              </button>
            </div>
          </div>
        )}

        {/* Test email */}
        {emailConfigured && (
          <div style={{ marginTop: '1.25rem', paddingTop: '1.25rem', borderTop: '1px solid #e9ecef' }}>
            <h4 style={{ margin: '0 0 0.5rem', fontSize: '0.95rem' }}>Send test email</h4>
            <p style={{ margin: '0 0 0.75rem', fontSize: '0.875rem', color: '#7f8c8d' }}>
              Verify Resend is configured correctly. The test email will be sent to your verified address.
            </p>
            {testEmailError && <div className="error-message" style={{ marginBottom: '0.75rem' }}>{testEmailError}</div>}
            {testEmailSuccess && <div className="success-message" style={{ marginBottom: '0.75rem' }}>{testEmailSuccess}</div>}
            <button className="btn btn-secondary" onClick={handleSendTestEmail} disabled={testEmailLoading || !myEmailVerified}>
              {testEmailLoading ? 'Sending…' : 'Send Test Email'}
            </button>
            {!myEmailVerified && (
              <small style={{ color: '#856404', marginLeft: '0.75rem' }}>
                Verify your email address above to enable this.
              </small>
            )}
          </div>
        )}
      </section>

      {/* ── Low-stock alerts section ──────────────────────────────────────── */}
      <section style={{ ...sectionStyle, marginTop: '1.5rem' }}>
        <h3 style={sectionHeadingStyle}>Low stock alerts</h3>
        <p style={{ margin: '0 0 1rem', fontSize: '0.875rem', color: '#7f8c8d' }}>
          Get an email when an item in your freezer falls to or below your chosen quantity.
          {!myEmailVerified && (
            <span style={{ color: '#856404' }}> (Add a verified email above to receive alerts.)</span>
          )}
        </p>

        {alertsError && <div className="error-message" style={{ marginBottom: '0.75rem' }}>{alertsError}</div>}

        {/* Add alert form */}
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-end', flexWrap: 'wrap', marginBottom: '1.25rem' }}>
          <div style={{ flex: '1 1 200px' }}>
            <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.25rem', color: '#495057' }}>
              Item name
            </label>
            <Autocomplete
              value={newItemName}
              onChange={setNewItemName}
              suggestions={itemNameSuggestions}
              placeholder="Type to search…"
              restricted
            />
            {itemNameSuggestions.length === 0 && (
              <small style={{ color: '#856404' }}>No items currently in the freezer.</small>
            )}
          </div>
          <div style={{ width: '110px' }}>
            <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.25rem', color: '#495057' }}>
              Alert when ≤
            </label>
            <input
              type="number"
              inputMode="numeric"
              value={newThreshold}
              onChange={(e) => setNewThreshold(e.target.value)}
              min={1}
              style={{ width: '100%', boxSizing: 'border-box' }}
            />
          </div>
          <button
            className="btn btn-primary"
            onClick={handleAddAlert}
            disabled={
              addLoading ||
              !itemNameSuggestions.some(
                (s) => s.toLowerCase() === newItemName.trim().toLowerCase()
              )
            }
            style={{ alignSelf: 'flex-end' }}
          >
            {addLoading ? 'Adding…' : 'Add alert'}
          </button>
        </div>
        {addError && <div className="error-message" style={{ marginBottom: '0.75rem' }}>{addError}</div>}

        {/* Alert list */}
        {alertsLoading ? (
          <p style={{ color: '#7f8c8d', fontSize: '0.9rem' }}>Loading alerts…</p>
        ) : alerts.length === 0 ? (
          <p style={{ color: '#7f8c8d', fontSize: '0.9rem', fontStyle: 'italic' }}>
            No low-stock alerts yet.
          </p>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #e9ecef', textAlign: 'left' }}>
                <th style={thStyle}>Item</th>
                <th style={{ ...thStyle, width: '120px' }}>Alert when ≤</th>
                <th style={{ ...thStyle, width: '80px' }}>Enabled</th>
                <th style={{ ...thStyle, width: '60px' }}></th>
              </tr>
            </thead>
            <tbody>
              {alerts.map(alert => (
                <tr key={alert.id} style={{ borderBottom: '1px solid #f0f0f0' }}>
                  <td style={tdStyle}>{alert.item_name}</td>
                  <td style={tdStyle}>
                    <input
                      type="number"
                      inputMode="numeric"
                      defaultValue={alert.threshold}
                      min={1}
                      onBlur={(e) => handleThresholdChange(alert, e.target.value)}
                      style={{ width: '70px', padding: '0.25rem 0.4rem', border: '1px solid #ced4da', borderRadius: '4px' }}
                    />
                  </td>
                  <td style={tdStyle}>
                    <input
                      type="checkbox"
                      checked={alert.enabled}
                      onChange={() => handleToggleEnabled(alert)}
                      style={{ cursor: 'pointer', width: '16px', height: '16px' }}
                    />
                  </td>
                  <td style={tdStyle}>
                    <button
                      onClick={() => handleDeleteAlert(alert.id)}
                      style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#dc3545', fontSize: '1rem', padding: '0.2rem 0.4rem' }}
                      title="Delete alert"
                    >
                      ✕
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const sectionStyle = {
  background: 'white',
  borderRadius: '8px',
  border: '1px solid #e9ecef',
  padding: '1.5rem',
};

const sectionHeadingStyle = {
  margin: '0 0 1rem',
  fontSize: '1.05rem',
  paddingBottom: '0.75rem',
  borderBottom: '1px solid #e9ecef',
};

const warningBannerStyle = {
  padding: '0.75rem 1rem',
  background: '#fff3cd',
  border: '1px solid #ffc107',
  borderRadius: '4px',
  marginBottom: '1rem',
  fontSize: '0.9rem',
  color: '#856404',
};

const verifiedBadgeStyle = {
  fontSize: '0.75rem',
  background: '#d4edda',
  color: '#155724',
  padding: '0.15rem 0.5rem',
  borderRadius: '3px',
  fontWeight: '600',
};

const unverifiedBadgeStyle = {
  fontSize: '0.75rem',
  background: '#fff3cd',
  color: '#856404',
  padding: '0.15rem 0.5rem',
  borderRadius: '3px',
  fontWeight: '600',
};

const thStyle = {
  padding: '0.5rem 0.75rem',
  fontWeight: '600',
  color: '#495057',
  fontSize: '0.85rem',
};

const tdStyle = {
  padding: '0.6rem 0.75rem',
  verticalAlign: 'middle',
};

export default EmailNotifications;
