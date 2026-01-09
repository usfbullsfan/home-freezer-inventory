import { useState, useEffect } from 'react';
import { authAPI } from '../services/api';

function UserManagement({ currentUser }) {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showResetPasswordModal, setShowResetPasswordModal] = useState(false);
  const [showActivationCodeModal, setShowActivationCodeModal] = useState(false);
  const [showRegenerateModal, setShowRegenerateModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [activationCode, setActivationCode] = useState('');

  const [newUser, setNewUser] = useState({
    username: '',
    role: 'user',
  });

  const [editUser, setEditUser] = useState({
    username: '',
    role: 'user',
  });

  const [resetPassword, setResetPassword] = useState({
    new_password: '',
    confirm_password: '',
  });

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await authAPI.getUsers();
      setUsers(response.data);
    } catch (err) {
      setError('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const handleAddUser = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    try {
      const response = await authAPI.register(newUser.username, null, newUser.role);
      setActivationCode(response.data.activation_code);
      setShowAddModal(false);
      setShowActivationCodeModal(true);
      setNewUser({ username: '', role: 'user' });
      loadUsers();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to create user');
    }
  };

  const handleEditUser = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    try {
      await authAPI.updateUser(selectedUser.id, {
        username: editUser.username,
        role: editUser.role,
      });
      setSuccess('User updated successfully');
      setShowEditModal(false);
      setSelectedUser(null);
      loadUsers();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to update user');
    }
  };

  const handleDeleteUser = async (user) => {
    if (!window.confirm(`Are you sure you want to delete user "${user.username}"? This cannot be undone.`)) {
      return;
    }

    setError('');
    setSuccess('');

    try {
      await authAPI.deleteUser(user.id);
      setSuccess(`User "${user.username}" deleted successfully`);
      loadUsers();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to delete user');
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (resetPassword.new_password !== resetPassword.confirm_password) {
      setError('Passwords do not match');
      return;
    }

    if (resetPassword.new_password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }

    try {
      await authAPI.resetUserPassword(selectedUser.id, resetPassword.new_password);
      setSuccess(`Password reset successfully for user "${selectedUser.username}"`);
      setShowResetPasswordModal(false);
      setSelectedUser(null);
      setResetPassword({ new_password: '', confirm_password: '' });
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to reset password');
    }
  };

  const openEditModal = (user) => {
    setSelectedUser(user);
    setEditUser({
      username: user.username,
      role: user.role,
    });
    setShowEditModal(true);
  };

  const openResetPasswordModal = (user) => {
    setSelectedUser(user);
    setResetPassword({ new_password: '', confirm_password: '' });
    setShowResetPasswordModal(true);
  };

  const handleRegenerateActivation = async (user) => {
    if (!window.confirm(`Regenerate activation code for "${user.username}"? This will invalidate any previous code and they will need to re-activate their account.`)) {
      return;
    }

    setError('');
    setSuccess('');

    try {
      const response = await authAPI.regenerateActivationCode(user.id);
      setActivationCode(response.data.activation_code);
      setSelectedUser(user);
      setShowRegenerateModal(true);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to regenerate activation code');
    }
  };

  if (loading) {
    return (
      <div style={{ background: 'white', padding: '2rem', borderRadius: '8px', marginTop: '2rem' }}>
        <div className="loading">Loading users...</div>
      </div>
    );
  }

  return (
    <>
      <div style={{ background: 'white', padding: '2rem', borderRadius: '8px', marginTop: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h3 style={{ margin: 0 }}>User Management</h3>
          <button className="btn btn-primary" onClick={() => setShowAddModal(true)}>
            + Add User
          </button>
        </div>

        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}

        <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '1rem' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #ecf0f1' }}>
              <th style={{ textAlign: 'left', padding: '0.75rem' }}>Username</th>
              <th style={{ textAlign: 'left', padding: '0.75rem' }}>Role</th>
              <th style={{ textAlign: 'left', padding: '0.75rem' }}>Created</th>
              <th style={{ textAlign: 'right', padding: '0.75rem' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id} style={{ borderBottom: '1px solid #ecf0f1' }}>
                <td style={{ padding: '0.75rem' }}>
                  {user.username}
                  {user.id === currentUser.id && (
                    <span style={{ marginLeft: '0.5rem', color: '#3498db', fontSize: '0.8rem' }}>(You)</span>
                  )}
                </td>
                <td style={{ padding: '0.75rem' }}>
                  <span style={{
                    padding: '0.25rem 0.5rem',
                    borderRadius: '4px',
                    fontSize: '0.8rem',
                    background: user.role === 'admin' ? '#e74c3c' : '#95a5a6',
                    color: 'white',
                  }}>
                    {user.role}
                  </span>
                </td>
                <td style={{ padding: '0.75rem', color: '#7f8c8d', fontSize: '0.9rem' }}>
                  {new Date(user.created_at).toLocaleDateString()}
                </td>
                <td style={{ padding: '0.75rem', textAlign: 'right' }}>
                  <button
                    className="btn btn-sm"
                    onClick={() => openEditModal(user)}
                    style={{ marginRight: '0.5rem', fontSize: '0.8rem' }}
                  >
                    Edit
                  </button>
                  <button
                    className="btn btn-sm"
                    onClick={() => handleRegenerateActivation(user)}
                    style={{ marginRight: '0.5rem', fontSize: '0.8rem' }}
                  >
                    Regenerate Code
                  </button>
                  {user.id === currentUser.id ? (
                    <button
                      className="btn btn-sm"
                      onClick={() => openResetPasswordModal(user)}
                      style={{ marginRight: '0.5rem', fontSize: '0.8rem' }}
                    >
                      Reset Password
                    </button>
                  ) : (
                    <button
                      className="btn btn-sm btn-danger"
                      onClick={() => handleDeleteUser(user)}
                      style={{ fontSize: '0.8rem' }}
                    >
                      Delete
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {users.length === 0 && (
          <div style={{ textAlign: 'center', padding: '2rem', color: '#7f8c8d' }}>
            No users found
          </div>
        )}
      </div>

      {/* Add User Modal */}
      {showAddModal && (
        <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '500px' }}>
            <div className="modal-header">
              <h3>Add New User</h3>
              <button className="close-btn" onClick={() => setShowAddModal(false)}>×</button>
            </div>
            <form onSubmit={handleAddUser}>
              <div className="modal-body">
                <p style={{ color: '#7f8c8d', fontSize: '0.9rem', marginBottom: '1rem' }}>
                  A one-time activation code will be generated for the user to set up their passkey.
                </p>

                <div className="form-group">
                  <label htmlFor="new-username">Username</label>
                  <input
                    type="text"
                    id="new-username"
                    value={newUser.username}
                    onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                    required
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="new-role">Role</label>
                  <select
                    id="new-role"
                    value={newUser.role}
                    onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                  >
                    <option value="user">User</option>
                    <option value="admin">Admin</option>
                  </select>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn" onClick={() => setShowAddModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Add User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit User Modal */}
      {showEditModal && selectedUser && (
        <div className="modal-overlay" onClick={() => setShowEditModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '500px' }}>
            <div className="modal-header">
              <h3>Edit User: {selectedUser.username}</h3>
              <button className="close-btn" onClick={() => setShowEditModal(false)}>×</button>
            </div>
            <form onSubmit={handleEditUser}>
              <div className="modal-body">
                <div className="form-group">
                  <label htmlFor="edit-username">Username</label>
                  <input
                    type="text"
                    id="edit-username"
                    value={editUser.username}
                    onChange={(e) => setEditUser({ ...editUser, username: e.target.value })}
                    required
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="edit-role">Role</label>
                  <select
                    id="edit-role"
                    value={editUser.role}
                    onChange={(e) => setEditUser({ ...editUser, role: e.target.value })}
                  >
                    <option value="user">User</option>
                    <option value="admin">Admin</option>
                  </select>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn" onClick={() => setShowEditModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Update User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Reset Password Modal */}
      {showResetPasswordModal && selectedUser && (
        <div className="modal-overlay" onClick={() => setShowResetPasswordModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '500px' }}>
            <div className="modal-header">
              <h3>Reset Password: {selectedUser.username}</h3>
              <button className="close-btn" onClick={() => setShowResetPasswordModal(false)}>×</button>
            </div>
            <form onSubmit={handleResetPassword}>
              <div className="modal-body">
                <div className="form-group">
                  <label htmlFor="reset-password">New Password</label>
                  <input
                    type="password"
                    id="reset-password"
                    value={resetPassword.new_password}
                    onChange={(e) => setResetPassword({ ...resetPassword, new_password: e.target.value })}
                    required
                    minLength="6"
                  />
                  <small style={{ color: '#7f8c8d', display: 'block', marginTop: '0.25rem' }}>
                    Must be at least 6 characters
                  </small>
                </div>

                <div className="form-group">
                  <label htmlFor="reset-confirm-password">Confirm New Password</label>
                  <input
                    type="password"
                    id="reset-confirm-password"
                    value={resetPassword.confirm_password}
                    onChange={(e) => setResetPassword({ ...resetPassword, confirm_password: e.target.value })}
                    required
                    minLength="6"
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn" onClick={() => setShowResetPasswordModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Reset Password
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Activation Code Modal */}
      {showActivationCodeModal && (
        <div className="modal-overlay" onClick={() => setShowActivationCodeModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '500px' }}>
            <div className="modal-header">
              <h3>✅ User Created Successfully</h3>
              <button className="close-btn" onClick={() => setShowActivationCodeModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <p style={{ color: '#7f8c8d', marginBottom: '1rem' }}>
                Share this activation code with the user. They will use it to set up their passkey.
                <strong style={{ display: 'block', marginTop: '0.5rem', color: '#e74c3c' }}>
                  This code will only be shown once!
                </strong>
              </p>

              <div style={{
                background: '#f8f9fa',
                padding: '1.5rem',
                borderRadius: '4px',
                border: '2px solid #3498db',
                textAlign: 'center',
                marginBottom: '1rem'
              }}>
                <div style={{
                  fontSize: '2rem',
                  fontFamily: 'monospace',
                  letterSpacing: '0.3em',
                  fontWeight: 'bold',
                  color: '#2c3e50'
                }}>
                  {activationCode}
                </div>
              </div>

              <button
                className="btn btn-secondary"
                onClick={() => {
                  navigator.clipboard.writeText(activationCode);
                  setSuccess('Activation code copied to clipboard!');
                }}
                style={{ width: '100%', marginBottom: '0.5rem' }}
              >
                📋 Copy to Clipboard
              </button>
            </div>
            <div className="modal-footer">
              <button
                className="btn btn-primary"
                onClick={() => {
                  setShowActivationCodeModal(false);
                  setActivationCode('');
                }}
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Regenerate Activation Code Modal */}
      {showRegenerateModal && selectedUser && (
        <div className="modal-overlay" onClick={() => setShowRegenerateModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '500px' }}>
            <div className="modal-header">
              <h3>🔄 Activation Code Regenerated</h3>
              <button className="close-btn" onClick={() => setShowRegenerateModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <p style={{ color: '#7f8c8d', marginBottom: '1rem' }}>
                New activation code for <strong>{selectedUser.username}</strong>:
                <strong style={{ display: 'block', marginTop: '0.5rem', color: '#e74c3c' }}>
                  This code will only be shown once!
                </strong>
              </p>

              <div style={{
                background: '#f8f9fa',
                padding: '1.5rem',
                borderRadius: '4px',
                border: '2px solid #e67e22',
                textAlign: 'center',
                marginBottom: '1rem'
              }}>
                <div style={{
                  fontSize: '2rem',
                  fontFamily: 'monospace',
                  letterSpacing: '0.3em',
                  fontWeight: 'bold',
                  color: '#2c3e50'
                }}>
                  {activationCode}
                </div>
              </div>

              <button
                className="btn btn-secondary"
                onClick={() => {
                  navigator.clipboard.writeText(activationCode);
                  setSuccess('Activation code copied to clipboard!');
                }}
                style={{ width: '100%', marginBottom: '0.5rem' }}
              >
                📋 Copy to Clipboard
              </button>
            </div>
            <div className="modal-footer">
              <button
                className="btn btn-primary"
                onClick={() => {
                  setShowRegenerateModal(false);
                  setActivationCode('');
                  setSelectedUser(null);
                  loadUsers(); // Refresh user list
                }}
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default UserManagement;
