import { useNavigate } from 'react-router-dom';
import { getSessionItemCount, getSessionItemIds, clearSession } from '../utils/sessionTracking';
import './SessionBanner.css';

function SessionBanner() {
  const navigate = useNavigate();
  const itemCount = getSessionItemCount();

  if (itemCount === 0) {
    return null;
  }

  const handlePrintLabels = () => {
    const itemIds = getSessionItemIds();
    // Navigate to print labels page with pre-selected items
    navigate('/print-labels', { state: { preSelectedItems: itemIds } });
    clearSession();
  };

  const handleDismiss = () => {
    clearSession();
    // Force a re-render by triggering a window event
    window.dispatchEvent(new Event('storage'));
  };

  return (
    <div className="session-banner">
      <div className="session-banner-content">
        <div className="session-banner-icon">🏷️</div>
        <div className="session-banner-text">
          <strong>You just added {itemCount} item{itemCount > 1 ? 's' : ''}!</strong>
          <span>Print QR code labels now?</span>
        </div>
        <div className="session-banner-actions">
          <button className="btn btn-primary" onClick={handlePrintLabels}>
            Print Labels
          </button>
          <button className="btn btn-secondary" onClick={handleDismiss}>
            Dismiss
          </button>
        </div>
      </div>
    </div>
  );
}

export default SessionBanner;
