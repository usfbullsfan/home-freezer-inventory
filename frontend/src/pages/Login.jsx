import { useState, useEffect } from 'react';
import { authAPI } from '../services/api';
import { loginWithPasskey, registerPasskey, supportsPasskeys, generateRecoveryCodes } from '../utils/passkey';
import '../App.css';

function Login({ setUser }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [activationCode, setActivationCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState('passkey'); // 'passkey', 'password', 'activate'
  const [recoveryCodes, setRecoveryCodes] = useState(null);
  const [showRecoveryCodes, setShowRecoveryCodes] = useState(false);

  // Check passkey support on mount
  useEffect(() => {
    if (!supportsPasskeys()) {
      setMode('password');
      setError('Your browser does not support passkeys. Using password login.');
    }
  }, []);

  const handlePasskeyLogin = async () => {
    setError('');
    setLoading(true);

    const result = await loginWithPasskey(username);

    if (result.success) {
      setUser(result.user);
    } else {
      setError(result.error);
    }

    setLoading(false);
  };

  const handleDiscoverablePasskeyLogin = async () => {
    setError('');
    setLoading(true);

    // Call without username for discoverable credential authentication
    const result = await loginWithPasskey(null);

    if (result.success) {
      setUser(result.user);
    } else {
      setError(result.error);
    }

    setLoading(false);
  };

  const handlePasswordLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await authAPI.login(username, password);
      const { token, user } = response.data;

      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify(user));

      setUser(user);
    } catch (err) {
      setError(err.response?.data?.error || 'Login failed');
    }

    setLoading(false);
  };

  const handleActivate = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Step 1: Activate account with activation code
      const response = await authAPI.activate(activationCode);
      const { token, user } = response.data;

      // Store token temporarily
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify(user));

      // Step 2: Register passkey
      const passkeyResult = await registerPasskey(user.username);

      if (!passkeyResult.success) {
        setError('Account activated but passkey registration failed. Please try adding a passkey in Settings.');
        setUser(user);
        setLoading(false);
        return;
      }

      // Step 3: Generate recovery codes
      const codesResult = await generateRecoveryCodes();

      if (codesResult.success) {
        setRecoveryCodes(codesResult.codes);
        setShowRecoveryCodes(true);
      }

      setUser(user);
    } catch (err) {
      setError(err.response?.data?.error || 'Activation failed');
    }

    setLoading(false);
  };

  const handleSaveRecoveryCodes = () => {
    setShowRecoveryCodes(false);
    setRecoveryCodes(null);
  };

  if (showRecoveryCodes && recoveryCodes) {
    return (
      <div className="login-container">
        <div className="login-box" style={{ maxWidth: '600px' }}>
          <h2>⚠️ Save Your Recovery Codes</h2>
          <p style={{ color: '#666', marginBottom: '1rem' }}>
            These codes can be used to access your account if you lose your passkey.
            <strong> Save them somewhere safe - they won't be shown again!</strong>
          </p>

          <div style={{
            background: '#f5f5f5',
            padding: '1rem',
            borderRadius: '4px',
            fontFamily: 'monospace',
            fontSize: '14px',
            marginBottom: '1rem'
          }}>
            {recoveryCodes.map((code, idx) => (
              <div key={idx} style={{ padding: '0.25rem 0' }}>
                {idx + 1}. {code}
              </div>
            ))}
          </div>

          <button
            onClick={handleSaveRecoveryCodes}
            className="btn btn-primary"
            style={{ width: '100%' }}
          >
            I've Saved These Codes
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="login-container">
      <div className="login-box">
        <h1 className="login-title">Freezer Inventory</h1>
        <p className="login-subtitle">Track and manage your freezer items</p>

        {error && (
          <div className="error-message" style={{ marginBottom: '1rem' }}>
            {error}
          </div>
        )}

        {mode === 'passkey' ? (
          // Passkey Login (Primary)
          <div>
            <h2 style={{ marginBottom: '1.5rem', textAlign: 'center' }}>Sign In</h2>

            <button
              onClick={handleDiscoverablePasskeyLogin}
              disabled={loading}
              className="btn btn-primary"
              style={{
                width: '100%',
                padding: '0.75rem',
                fontSize: '1.1rem',
                marginBottom: '1rem'
              }}
            >
              {loading ? '🔐 Authenticating...' : '🔐 Sign in with Passkey'}
            </button>

            <div style={{
              display: 'flex',
              alignItems: 'center',
              margin: '1.5rem 0',
              color: '#999'
            }}>
              <div style={{ flex: 1, height: '1px', background: '#ddd' }}></div>
              <div style={{ padding: '0 1rem', fontSize: '0.9rem' }}>or</div>
              <div style={{ flex: 1, height: '1px', background: '#ddd' }}></div>
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <label htmlFor="username" style={{ fontSize: '0.9rem', color: '#666' }}>
                Sign in with username
              </label>
              <input
                type="text"
                id="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your username"
                disabled={loading}
                style={{ width: '100%' }}
              />
            </div>

            <button
              onClick={handlePasskeyLogin}
              disabled={loading || !username}
              className="btn btn-secondary"
              style={{
                width: '100%',
                padding: '0.75rem',
                fontSize: '1rem',
                marginBottom: '1.5rem',
                background: 'white',
                color: '#2c3e50',
                border: '1px solid #ddd'
              }}
            >
              {loading ? '🔐 Authenticating...' : '🔐 Sign in with Username + Passkey'}
            </button>

            <div style={{ textAlign: 'center', color: '#666', marginBottom: '1rem' }}>
              <small>
                Have an activation code? <button
                  onClick={() => setMode('activate')}
                  className="link-button"
                  disabled={loading}
                >
                  Activate Account
                </button>
              </small>
            </div>

            <div style={{ textAlign: 'center', color: '#999', fontSize: '0.9rem' }}>
              <button
                onClick={() => setMode('password')}
                className="link-button"
                disabled={loading}
              >
                Use password instead
              </button>
            </div>
          </div>
        ) : mode === 'password' ? (
          // Password Login (Fallback)
          <form onSubmit={handlePasswordLogin}>
            <h2 style={{ marginBottom: '1.5rem', textAlign: 'center' }}>Password Login</h2>

            <div style={{ marginBottom: '1rem' }}>
              <label htmlFor="username-pwd">Username</label>
              <input
                type="text"
                id="username-pwd"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                disabled={loading}
                style={{ width: '100%' }}
              />
            </div>

            <div style={{ marginBottom: '1.5rem' }}>
              <label htmlFor="password">Password</label>
              <input
                type="password"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={loading}
                style={{ width: '100%' }}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn btn-primary"
              style={{ width: '100%', marginBottom: '1rem' }}
            >
              {loading ? 'Logging in...' : 'Login'}
            </button>

            {supportsPasskeys() && (
              <div style={{ textAlign: 'center', color: '#999', fontSize: '0.9rem' }}>
                <button
                  type="button"
                  onClick={() => setMode('passkey')}
                  className="link-button"
                  disabled={loading}
                >
                  ← Back to passkey login
                </button>
              </div>
            )}
          </form>
        ) : (
          // Activation
          <form onSubmit={handleActivate}>
            <h2 style={{ marginBottom: '1.5rem', textAlign: 'center' }}>Activate Account</h2>
            <p style={{ color: '#666', fontSize: '0.9rem', marginBottom: '1rem', textAlign: 'center' }}>
              Enter the activation code provided by your administrator to set up your passkey
            </p>

            <div style={{ marginBottom: '1.5rem' }}>
              <label htmlFor="activation-code">Activation Code</label>
              <input
                type="text"
                id="activation-code"
                value={activationCode}
                onChange={(e) => setActivationCode(e.target.value.toUpperCase())}
                required
                disabled={loading}
                style={{ width: '100%', fontFamily: 'monospace', letterSpacing: '0.1em' }}
                placeholder="XXXXXXXX"
                maxLength={8}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn btn-primary"
              style={{ width: '100%', marginBottom: '1rem' }}
            >
              {loading ? 'Activating Account...' : 'Activate & Setup Passkey'}
            </button>

            <div style={{ textAlign: 'center', color: '#999', fontSize: '0.9rem' }}>
              <button
                type="button"
                onClick={() => setMode('passkey')}
                className="link-button"
                disabled={loading}
              >
                ← Back to login
              </button>
            </div>
          </form>
        )}
      </div>

      <style jsx>{`
        .link-button {
          background: none;
          border: none;
          color: inherit;
          cursor: pointer;
          text-decoration: underline;
          padding: 0;
          font: inherit;
        }

        .link-button:hover:not(:disabled) {
          color: #1976d2;
        }

        .link-button:disabled {
          cursor: not-allowed;
          opacity: 0.5;
        }
      `}</style>
    </div>
  );
}

export default Login;
