import { useState, useEffect } from 'react';
import { feedbackAPI } from '../services/api';

function FeedbackManagement() {
  const [feedback, setFeedback] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError('');

    try {
      const [feedbackResponse, statsResponse] = await Promise.all([
        feedbackAPI.list(),
        feedbackAPI.getStats()
      ]);

      setFeedback(feedbackResponse.data.feedback);
      setStats(statsResponse.data);
    } catch (err) {
      setError('Failed to load feedback data');
      console.error(err);
    }

    setLoading(false);
  };

  const handleProcess = async () => {
    if (!confirm('Process all pending feedback and create GitHub issues?')) {
      return;
    }

    setProcessing(true);
    setError('');
    setMessage('');

    try {
      const response = await feedbackAPI.process();

      if (response.data.success) {
        setMessage('GitHub issues created successfully!');
        // Reload data
        await loadData();
      } else {
        setError(response.data.error || 'Processing failed');
      }
    } catch (err) {
      // Show error with details if available
      const errorMsg = err.response?.data?.error || 'Failed to process feedback';
      const details = err.response?.data?.details;
      setError(details ? `${errorMsg}\n\n${details}` : errorMsg);
    }

    setProcessing(false);
  };

  const getStatusBadge = (status) => {
    const styles = {
      pending: { background: '#f39c12', color: 'white' },
      processed: { background: '#27ae60', color: 'white' },
      failed: { background: '#e74c3c', color: 'white' }
    };

    const labels = {
      pending: '⏳ Pending',
      processed: '✅ Processed',
      failed: '❌ Failed'
    };

    return (
      <span style={{
        padding: '0.25rem 0.5rem',
        borderRadius: '4px',
        fontSize: '0.8rem',
        fontWeight: 'bold',
        ...styles[status]
      }}>
        {labels[status]}
      </span>
    );
  };

  const getTypeBadge = (type) => {
    return type === 'bug'
      ? <span style={{ fontSize: '1.2rem' }}>🐛</span>
      : <span style={{ fontSize: '1.2rem' }}>✨</span>;
  };

  if (loading) {
    return <div>Loading feedback...</div>;
  }

  return (
    <div className="settings-section">
      <h3>🐛 Feedback Management</h3>

      {stats && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
          gap: '1rem',
          marginBottom: '1.5rem'
        }}>
          <div style={{ background: '#ecf0f1', padding: '1rem', borderRadius: '8px', textAlign: 'center' }}>
            <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#2c3e50' }}>{stats.total}</div>
            <div style={{ fontSize: '0.9rem', color: '#7f8c8d' }}>Total</div>
          </div>
          <div style={{ background: '#fff3cd', padding: '1rem', borderRadius: '8px', textAlign: 'center' }}>
            <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#f39c12' }}>{stats.pending}</div>
            <div style={{ fontSize: '0.9rem', color: '#856404' }}>Pending</div>
          </div>
          <div style={{ background: '#d4edda', padding: '1rem', borderRadius: '8px', textAlign: 'center' }}>
            <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#27ae60' }}>{stats.processed}</div>
            <div style={{ fontSize: '0.9rem', color: '#155724' }}>Processed</div>
          </div>
          <div style={{ background: '#f8d7da', padding: '1rem', borderRadius: '8px', textAlign: 'center' }}>
            <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#e74c3c' }}>{stats.failed}</div>
            <div style={{ fontSize: '0.9rem', color: '#721c24' }}>Failed</div>
          </div>
        </div>
      )}

      {error && (
        <div className="error-message" style={{ marginBottom: '1rem', whiteSpace: 'pre-wrap' }}>
          {error}
        </div>
      )}

      {message && (
        <div style={{
          background: '#d4edda',
          color: '#155724',
          padding: '0.75rem',
          borderRadius: '4px',
          marginBottom: '1rem'
        }}>
          {message}
        </div>
      )}

      <div style={{ marginBottom: '1.5rem' }}>
        <button
          onClick={handleProcess}
          disabled={processing || stats?.pending === 0}
          className="btn btn-primary"
          style={{ marginRight: '0.5rem' }}
        >
          {processing ? '⏳ Processing...' : '🚀 Process Pending Feedback'}
        </button>
        <button
          onClick={loadData}
          disabled={loading}
          className="btn btn-secondary"
        >
          🔄 Refresh
        </button>
        <p style={{ fontSize: '0.85rem', color: '#666', marginTop: '0.5rem' }}>
          Pending feedback is automatically processed hourly. Click "Process" to run manually.
        </p>
      </div>

      {feedback.length === 0 ? (
        <p style={{ color: '#999', fontStyle: 'italic' }}>No feedback submissions yet.</p>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table className="data-table" style={{ width: '100%', fontSize: '0.9rem' }}>
            <thead>
              <tr>
                <th style={{ width: '50px' }}>Type</th>
                <th style={{ width: '100px' }}>Status</th>
                <th>User</th>
                <th>Description</th>
                <th style={{ width: '120px' }}>Submitted</th>
                <th style={{ width: '80px' }}>GitHub</th>
              </tr>
            </thead>
            <tbody>
              {feedback.map((item) => (
                <tr key={item.id}>
                  <td style={{ textAlign: 'center' }}>{getTypeBadge(item.type)}</td>
                  <td>{getStatusBadge(item.status)}</td>
                  <td>{item.username}</td>
                  <td style={{ maxWidth: '300px' }}>
                    <div style={{
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}>
                      {item.description}
                    </div>
                  </td>
                  <td style={{ fontSize: '0.8rem', color: '#666' }}>
                    {new Date(item.submitted_at).toLocaleString()}
                  </td>
                  <td>
                    {item.github_issue_url ? (
                      <a
                        href={item.github_issue_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ fontSize: '0.9rem' }}
                      >
                        #{item.github_issue_number}
                      </a>
                    ) : (
                      item.status === 'failed' ? (
                        <span style={{ color: '#e74c3c', fontSize: '0.8rem' }} title={item.error_message}>
                          Error
                        </span>
                      ) : (
                        '-'
                      )
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default FeedbackManagement;
