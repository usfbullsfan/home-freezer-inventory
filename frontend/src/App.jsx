import { useState, useEffect, lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import './App.css';
import { clearSession } from './utils/sessionTracking';
import { isMobileDevice, isDesktopSiteRequested, getLogoPath } from './utils/deviceDetection';
import api from './services/api';
import FeedbackModal from './components/FeedbackModal';

// Lazy load route components for better code splitting
const Login = lazy(() => import('./pages/Login'));
const Inventory = lazy(() => import('./pages/Inventory'));
const Categories = lazy(() => import('./pages/Categories'));
const PrintLabels = lazy(() => import('./pages/PrintLabels'));
const Settings = lazy(() => import('./pages/Settings'));
const QRRedirect = lazy(() => import('./pages/QRRedirect'));
const MobileLanding = lazy(() => import('./pages/MobileLanding'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const InstallPrompt = lazy(() => import('./components/InstallPrompt'));

function AppContent() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [useDesktopInterface, setUseDesktopInterface] = useState(false);
  const [feedbackModalOpen, setFeedbackModalOpen] = useState(false);
  const [qrEnabled, setQrEnabled] = useState(true);
  const location = useLocation();
  const navigate = useNavigate();

  // Detect if running in development mode
  const isDev = import.meta.env.DEV;

  // Initial user check on mount
  useEffect(() => {
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
    }

    setLoading(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only run on mount

  // Save current URL for redirect after login
  useEffect(() => {
    if (!user && location.pathname !== '/') {
      sessionStorage.setItem('redirectAfterLogin', location.pathname + location.search);
    }
  }, [location, user]);

  // Fetch public feature flags whenever the logged-in user changes
  useEffect(() => {
    if (user) {
      api.get('/settings/features')
        .then(r => setQrEnabled(r.data.enable_qr_labels !== 'false'))
        .catch(() => setQrEnabled(true));
    }
  }, [user]);

  // Check mobile status and user preferences
  useEffect(() => {
    const checkMobileAndPreferences = async () => {
      // Detect if mobile device
      const mobileDetected = isMobileDevice();
      const desktopRequested = isDesktopSiteRequested();
      const newIsMobile = mobileDetected && !desktopRequested;

      // Only update if changed
      setIsMobile(prev => prev === newIsMobile ? prev : newIsMobile);

      // If user is logged in, check their desktop interface preference
      if (user) {
        try {
          const response = await api.get('/settings/user');
          const settings = response.data;
          const desktopPref = settings.find(s => s.setting_name === 'use_desktop_interface');

          const shouldUseDesktop = desktopPref && desktopPref.setting_value === 'true';
          setUseDesktopInterface(prev => prev === shouldUseDesktop ? prev : shouldUseDesktop);
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
      const newIsMobile = mobileDetected && !desktopRequested;
      setIsMobile(prev => prev === newIsMobile ? prev : newIsMobile);
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
        <Suspense fallback={<div className="loading">Loading...</div>}>
          <Login setUser={setUser} />
        </Suspense>
      ) : (
        <div className={`app ${showMobileInterface ? 'app-mobile' : ''}`}>
          {/* Install Prompt for mobile users */}
          {showMobileInterface && (
            <Suspense fallback={null}>
              <InstallPrompt />
            </Suspense>
          )}

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
              <h1>
                <img src={getLogoPath()} alt="Logo" className="navbar-logo" />
                Freezer Inventory
              </h1>
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
                    <Link to="/dashboard" onClick={() => setMobileMenuOpen(false)}>Dashboard</Link>
                    <details className="navbar-submenu">
                      <summary>Manage</summary>
                      <div className="navbar-submenu-items">
                        <Link to="/categories" onClick={() => setMobileMenuOpen(false)}>Categories</Link>
                        {qrEnabled && <Link to="/print-labels" onClick={() => setMobileMenuOpen(false)}>Print Labels</Link>}
                      </div>
                    </details>
                    <Link to="/settings" className="navbar-settings-link" onClick={() => setMobileMenuOpen(false)}>⚙️ Settings</Link>
                  </div>
                ) : (
                  // Desktop menu structure (unchanged)
                  <>
                    <Link to="/" onClick={() => setMobileMenuOpen(false)}>Inventory</Link>
                    <Link to="/dashboard" onClick={() => setMobileMenuOpen(false)}>Dashboard</Link>
                    <Link to="/categories" onClick={() => setMobileMenuOpen(false)}>Categories</Link>
                    {qrEnabled && <Link to="/print-labels" onClick={() => setMobileMenuOpen(false)}>Print Labels</Link>}
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

          <Suspense fallback={<div className="loading">Loading...</div>}>
            <Routes>
              {showMobileInterface ? (
                // Mobile routes
                <>
                  <Route path="/home" element={<MobileLanding qrEnabled={qrEnabled} />} />
                  <Route path="/" element={<Navigate to="/home" replace />} />
                  <Route path="/inventory" element={<Inventory isMobile={true} qrEnabled={qrEnabled} />} />
                  <Route path="/item/:qrCode" element={<QRRedirect />} />
                  <Route path="/dashboard" element={<Dashboard />} />
                  <Route path="/categories" element={<Categories />} />
                  <Route path="/print-labels" element={<PrintLabels />} />
                  <Route path="/settings" element={<Settings user={user} isMobile={true} setUseDesktopInterface={setUseDesktopInterface} />} />
                  <Route path="*" element={<Navigate to="/home" />} />
                </>
              ) : (
                // Desktop routes (unchanged)
                <>
                  <Route path="/" element={<Inventory qrEnabled={qrEnabled} />} />
                  <Route path="/item/:qrCode" element={<QRRedirect />} />
                  <Route path="/dashboard" element={<Dashboard />} />
                  <Route path="/categories" element={<Categories />} />
                  <Route path="/print-labels" element={<PrintLabels />} />
                  <Route path="/settings" element={<Settings user={user} />} />
                  <Route path="*" element={<Navigate to="/" />} />
                </>
              )}
            </Routes>
          </Suspense>

          {/* Floating Feedback Button */}
          <button
            onClick={() => setFeedbackModalOpen(true)}
            style={{
              position: 'fixed',
              bottom: '2rem',
              right: '2rem',
              padding: '0.75rem 1.25rem',
              background: '#3498db',
              color: 'white',
              border: 'none',
              borderRadius: '50px',
              cursor: 'pointer',
              fontSize: '0.9rem',
              fontWeight: 'bold',
              boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
              zIndex: 999,
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              transition: 'all 0.2s ease'
            }}
            onMouseEnter={(e) => {
              e.target.style.background = '#2980b9';
              e.target.style.transform = 'scale(1.05)';
            }}
            onMouseLeave={(e) => {
              e.target.style.background = '#3498db';
              e.target.style.transform = 'scale(1)';
            }}
            title="Report Bug or Request Feature"
          >
            <span style={{ fontSize: '1.1rem' }}>💬</span>
            <span>Feedback</span>
          </button>

          {/* Feedback Modal */}
          <FeedbackModal
            isOpen={feedbackModalOpen}
            onClose={() => setFeedbackModalOpen(false)}
          />
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
