import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { authAPI } from '../services/api';

function Login({ setUser }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  // Quick login state
  const [quickLoginEnabled, setQuickLoginEnabled] = useState(false);
  const [quickLoginUsers, setQuickLoginUsers] = useState([]);

  // Check if quick login is enabled on mount
  useEffect(() => {
    const checkQuickLogin = async () => {
      try {
        const response = await authAPI.getQuickLoginStatus();
        if (response.data.enabled) {
          setQuickLoginEnabled(true);
          // Fetch users for quick login
          const usersResponse = await authAPI.getQuickLoginUsers();
          setQuickLoginUsers(usersResponse.data);
        }
      } catch (err) {
        // Quick login not available, continue with normal login
        console.log('Quick login not available');
      }
    };

    checkQuickLogin();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await authAPI.login(username, password);
      const { access_token, user } = response.data;

      // Store token and user
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(user));

      setUser(user);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.error || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = async (userId) => {
    setError('');
    setLoading(true);

    try {
      const response = await authAPI.quickLogin(userId);
      const { access_token, user } = response.data;

      // Store token and user
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(user));

      setUser(user);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.error || 'Quick login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <h2>🧊 Freezer Inventory Tracker</h2>

        {error && <div className="error-message">{error}</div>}

        {quickLoginEnabled && quickLoginUsers.length > 0 && (
          <div style={{ marginBottom: '2rem' }}>
            <div
              style={{
                background: 'linear-gradient(135deg, #ff6b6b 0%, #ff8c42 100%)',
                color: 'white',
                padding: '0.75rem',
                borderRadius: '4px',
                marginBottom: '1rem',
                textAlign: 'center',
                fontWeight: 'bold',
              }}
            >
              ⚠️ DEV MODE - Quick Login Enabled
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {quickLoginUsers.map((user) => (
                <button
                  key={user.id}
                  className={`btn ${user.role === 'admin' ? 'btn-danger' : 'btn-secondary'}`}
                  onClick={() => handleQuickLogin(user.id)}
                  disabled={loading}
                  style={{ width: '100%' }}
                >
                  Login as {user.username} {user.role === 'admin' && '(Admin)'}
                </button>
              ))}
            </div>
            <div
              style={{
                textAlign: 'center',
                margin: '1rem 0',
                color: '#7f8c8d',
                fontSize: '0.875rem',
              }}
            >
              — OR —
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoFocus={!quickLoginEnabled}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading}
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>
      </div>
    </div>
  );
}

export default Login;
