import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';
import './App.css';

import Login from './pages/Login';
import Inventory from './pages/Inventory';
import Categories from './pages/Categories';
import PrintLabels from './pages/PrintLabels';
import Settings from './pages/Settings';

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is logged in
    const storedUser = localStorage.getItem('user');
    const token = localStorage.getItem('token');

    if (storedUser && token) {
      setUser(JSON.parse(storedUser));
    }

    setLoading(false);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  };

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  return (
    <Router>
      {!user ? (
        <Login setUser={setUser} />
      ) : (
        <div className="app">
          <nav className="navbar">
            <h1>🧊 Freezer Inventory</h1>
            <nav>
              <Link to="/">Inventory</Link>
              <Link to="/categories">Categories</Link>
              <Link to="/print-labels">Print Labels</Link>
              <Link to="/settings">Settings</Link>
            </nav>
            <div className="user-info">
              <span>
                {user.username} {user.role === 'admin' && '(Admin)'}
              </span>
              <button onClick={handleLogout}>Logout</button>
            </div>
          </nav>

          <Routes>
            <Route path="/" element={<Inventory />} />
            <Route path="/categories" element={<Categories />} />
            <Route path="/print-labels" element={<PrintLabels />} />
            <Route path="/settings" element={<Settings user={user} />} />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </div>
      )}
    </Router>
  );
}

export default App;
