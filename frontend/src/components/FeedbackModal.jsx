import { useState } from 'react';
import './Modal.css';

function FeedbackModal({ isOpen, onClose }) {
  const [type, setType] = useState('bug');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    // Validation
    if (!description.trim() || description.trim().length < 10) {
      setError('Please provide at least 10 characters describing the issue or request');
      setLoading(false);
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/feedback/submit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          type,
          description: description.trim()
        })
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess(true);
        setTimeout(() => {
          onClose();
          // Reset form
          setDescription('');
          setType('bug');
          setSuccess(false);
        }, 2000);
      } else {
        setError(data.error || 'Failed to submit feedback');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    }

    setLoading(false);
  };

  const handleClose = () => {
    if (!loading) {
      setDescription('');
      setType('bug');
      setError('');
      setSuccess(false);
      onClose();
    }
  };

  if (!isOpen) return null;

  if (success) {
    return (
      <div className="modal-overlay" onClick={handleClose}>
        <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '500px' }}>
          <div style={{ textAlign: 'center', padding: '2rem' }}>
            <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>✅</div>
            <h2 style={{ color: '#27ae60', marginBottom: '0.5rem' }}>Thank You!</h2>
            <p style={{ color: '#666' }}>
              Your feedback has been submitted and will be reviewed shortly.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '600px' }}>
        <div className="modal-header">
          <h2>🐛 Report Bug / ✨ Request Feature</h2>
          <button onClick={handleClose} className="modal-close" disabled={loading}>×</button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <p style={{ color: '#666', marginBottom: '1.5rem' }}>
              Help us improve the Freezer Inventory Tracker! Your feedback will create a GitHub issue
              for our development team to review.
            </p>

            {error && (
              <div className="error-message" style={{ marginBottom: '1rem' }}>
                {error}
              </div>
            )}

            <div className="form-group">
              <label style={{ fontWeight: 'bold', marginBottom: '0.5rem', display: 'block' }}>
                What type of feedback are you submitting?
              </label>
              <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem' }}>
                <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                  <input
                    type="radio"
                    name="type"
                    value="bug"
                    checked={type === 'bug'}
                    onChange={(e) => setType(e.target.value)}
                    disabled={loading}
                    style={{ marginRight: '0.5rem' }}
                  />
                  🐛 Bug Report
                </label>
                <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                  <input
                    type="radio"
                    name="type"
                    value="enhancement"
                    checked={type === 'enhancement'}
                    onChange={(e) => setType(e.target.value)}
                    disabled={loading}
                    style={{ marginRight: '0.5rem' }}
                  />
                  ✨ Feature Request
                </label>
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="description" style={{ fontWeight: 'bold', marginBottom: '0.5rem', display: 'block' }}>
                {type === 'bug' ? 'Describe the bug' : 'Describe the feature you\'d like'}
              </label>
              <textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder={type === 'bug'
                  ? 'Please describe what happened, what you expected to happen, and any steps to reproduce the issue...'
                  : 'Please describe the feature you\'d like to see and how it would help you...'}
                required
                disabled={loading}
                rows={8}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  fontFamily: 'inherit',
                  fontSize: '0.9rem',
                  resize: 'vertical'
                }}
                minLength={10}
                maxLength={5000}
              />
              <small style={{ color: '#999', marginTop: '0.25rem', display: 'block' }}>
                {description.length}/5000 characters (minimum 10)
              </small>
            </div>
          </div>

          <div className="modal-footer">
            <button
              type="button"
              onClick={handleClose}
              disabled={loading}
              className="btn btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || description.trim().length < 10}
              className="btn btn-primary"
            >
              {loading ? 'Submitting...' : 'Submit Feedback'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default FeedbackModal;
