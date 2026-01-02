import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import './App.css';
import { clearSession } from './utils/sessionTracking';

import Login from './pages/Login';
import Inventory from './pages/Inventory';
import Categories from './pages/Categories';
import PrintLabels from './pages/PrintLabels';
import Settings from './pages/Settings';
import QRRedirect from './pages/QRRedirect';

function AppContent() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  // Detect if running in development mode
  const isDev = import.meta.env.DEV;

  useEffect(() => {
    // Check if user is logged in
    const storedUser = localStorage.getItem('user');
    const token = localStorage.getItem('token');

    if (storedUser && token) {
      setUser(JSON.parse(storedUser));

      // Check if there's a redirect URL saved
      const redirectUrl = sessionStorage.getItem('redirectAfterLogin');
      if (redirectUrl) {
        sessionStorage.removeItem('redirectAfterLogin');
        navigate(redirectUrl);
      }
    } else {
      // Not logged in - save current URL if it's not the home page
      if (location.pathname !== '/') {
        sessionStorage.setItem('redirectAfterLogin', location.pathname + location.search);
      }
    }

    setLoading(false);
  }, [location, navigate]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    sessionStorage.removeItem('redirectAfterLogin');
    clearSession(); // Clear recently added items session
    setUser(null);
  };

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  return (
    <>
      {!user ? (
        <Login setUser={setUser} />
      ) : (
        <div className="app">
          {isDev && (
            <div className="dev-banner">
              ⚠️ DEVELOPMENT ENVIRONMENT
            </div>
          )}
          <nav className={`navbar ${isDev ? 'navbar-dev' : ''}`}>
            <div className="navbar-header">
              <h1>🧊 Freezer Inventory</h1>
              <button
                className="mobile-menu-toggle"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                aria-label="Toggle menu"
              >
                {mobileMenuOpen ? '✕' : '☰'}
              </button>
            </div>
            <div className={`navbar-content ${mobileMenuOpen ? 'mobile-open' : ''}`}>
              <nav className="navbar-links">
                <Link to="/" onClick={() => setMobileMenuOpen(false)}>Inventory</Link>
                <Link to="/categories" onClick={() => setMobileMenuOpen(false)}>Categories</Link>
                <Link to="/print-labels" onClick={() => setMobileMenuOpen(false)}>Print Labels</Link>
                <Link to="/settings" onClick={() => setMobileMenuOpen(false)}>Settings</Link>
              </nav>
              <div className="user-info">
                <span>
                  {user.username} {user.role === 'admin' && '(Admin)'}
                </span>
                <button onClick={handleLogout}>Logout</button>
              </div>
            </div>
          </nav>

          <Routes>
            <Route path="/" element={<Inventory />} />
            <Route path="/item/:qrCode" element={<QRRedirect />} />
            <Route path="/categories" element={<Categories />} />
            <Route path="/print-labels" element={<PrintLabels />} />
            <Route path="/settings" element={<Settings user={user} />} />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </div>
      )}
    </>
  );
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;
