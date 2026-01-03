import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import './App.css';
import { clearSession } from './utils/sessionTracking';
import { isMobileDevice, isDesktopSiteRequested } from './utils/deviceDetection';
import api from './services/api';

import Login from './pages/Login';
import Inventory from './pages/Inventory';
import Categories from './pages/Categories';
import PrintLabels from './pages/PrintLabels';
import Settings from './pages/Settings';
import QRRedirect from './pages/QRRedirect';
import MobileLanding from './pages/MobileLanding';
import InstallPrompt from './components/InstallPrompt';

function AppContent() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [useDesktopInterface, setUseDesktopInterface] = useState(false);
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

  // Check mobile status and user preferences
  useEffect(() => {
    const checkMobileAndPreferences = async () => {
      // Detect if mobile device
      const mobileDetected = isMobileDevice();
      const desktopRequested = isDesktopSiteRequested();
      setIsMobile(mobileDetected && !desktopRequested);

      // If user is logged in, check their desktop interface preference
      if (user) {
        try {
          const response = await api.get('/api/settings/user');
          const settings = response.data;
          const desktopPref = settings.find(s => s.setting_name === 'use_desktop_interface');

          if (desktopPref && desktopPref.setting_value === 'true') {
            setUseDesktopInterface(true);
          }
        } catch (error) {
          console.error('Error fetching user preferences:', error);
        }
      }
    };

    checkMobileAndPreferences();

    // Re-check on window resize
    const handleResize = () => {
      const mobileDetected = isMobileDevice();
      const desktopRequested = isDesktopSiteRequested();
      setIsMobile(mobileDetected && !desktopRequested);
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [user]);

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

  // Determine if we should show mobile interface
  const showMobileInterface = isMobile && !useDesktopInterface;

  return (
    <>
      {!user ? (
        <Login setUser={setUser} />
      ) : (
        <div className={`app ${showMobileInterface ? 'app-mobile' : ''}`}>
          {/* Install Prompt for mobile users */}
          {showMobileInterface && <InstallPrompt />}

          {isDev && (
            <div className="dev-banner">
              ⚠️ DEVELOPMENT ENVIRONMENT
            </div>
          )}

          <nav className={`navbar ${isDev ? 'navbar-dev' : ''} ${showMobileInterface ? 'navbar-mobile' : ''}`}>
            <div className="navbar-header">
              {showMobileInterface && (
                <Link to="/home" className="navbar-home-icon" onClick={() => setMobileMenuOpen(false)}>
                  🏠
                </Link>
              )}
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
                {showMobileInterface ? (
                  // Mobile menu structure
                  <div className="mobile-menu-buttons">
                    <details className="navbar-submenu">
                      <summary>Manage</summary>
                      <div className="navbar-submenu-items">
                        <Link to="/categories" onClick={() => setMobileMenuOpen(false)}>Categories</Link>
                        <Link to="/print-labels" onClick={() => setMobileMenuOpen(false)}>Print Labels</Link>
                      </div>
                    </details>
                    <Link to="/settings" className="navbar-settings-link" onClick={() => setMobileMenuOpen(false)}>Settings</Link>
                  </div>
                ) : (
                  // Desktop menu structure (unchanged)
                  <>
                    <Link to="/" onClick={() => setMobileMenuOpen(false)}>Inventory</Link>
                    <Link to="/categories" onClick={() => setMobileMenuOpen(false)}>Categories</Link>
                    <Link to="/print-labels" onClick={() => setMobileMenuOpen(false)}>Print Labels</Link>
                    <Link to="/settings" onClick={() => setMobileMenuOpen(false)}>Settings</Link>
                  </>
                )}
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
            {showMobileInterface ? (
              // Mobile routes
              <>
                <Route path="/home" element={<MobileLanding />} />
                <Route path="/" element={<Navigate to="/home" replace />} />
                <Route path="/inventory" element={<Inventory isMobile={true} />} />
                <Route path="/item/:qrCode" element={<QRRedirect />} />
                <Route path="/categories" element={<Categories />} />
                <Route path="/print-labels" element={<PrintLabels />} />
                <Route path="/settings" element={<Settings user={user} isMobile={true} setUseDesktopInterface={setUseDesktopInterface} />} />
                <Route path="*" element={<Navigate to="/home" />} />
              </>
            ) : (
              // Desktop routes (unchanged)
              <>
                <Route path="/" element={<Inventory />} />
                <Route path="/item/:qrCode" element={<QRRedirect />} />
                <Route path="/categories" element={<Categories />} />
                <Route path="/print-labels" element={<PrintLabels />} />
                <Route path="/settings" element={<Settings user={user} />} />
                <Route path="*" element={<Navigate to="/" />} />
              </>
            )}
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
