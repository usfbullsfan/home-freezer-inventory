import { useNavigate } from 'react-router-dom';
import { getLogoPath, getAppName } from '../utils/deviceDetection';
import './MobileLanding.css';

/**
 * Mobile Landing Page
 * Simple, touch-friendly landing page for mobile users
 * Shows three main action buttons
 */
const MobileLanding = () => {
  const navigate = useNavigate();

  const actions = [
    {
      id: 'add',
      title: 'Add to Freezer',
      description: 'Add a new item to your freezer',
      icon: '➕',
      action: () => navigate('/inventory?action=add'),
      color: '#4caf50'
    },
    {
      id: 'search',
      title: 'Search Inventory',
      description: 'Browse and search your items',
      icon: '🔍',
      action: () => navigate('/inventory'),
      color: '#2196f3'
    },
    {
      id: 'scan',
      title: 'Scan QR Code',
      description: 'Locate an item by scanning its code',
      icon: '📷',
      action: () => navigate('/inventory?action=scan'),
      color: '#ff9800'
    }
  ];

  return (
    <div className="mobile-landing">
      <div className="mobile-landing-header">
        <img src={getLogoPath()} alt="Logo" className="mobile-landing-logo" />
        <h1 className="mobile-landing-title">{getAppName()}</h1>
      </div>

      <div className="mobile-landing-actions">
        {actions.map(action => (
          <button
            key={action.id}
            className="mobile-landing-button"
            onClick={action.action}
            style={{ '--button-color': action.color }}
          >
            <div className="mobile-landing-button-icon">{action.icon}</div>
            <div className="mobile-landing-button-content">
              <h2 className="mobile-landing-button-title">{action.title}</h2>
              <p className="mobile-landing-button-description">{action.description}</p>
            </div>
            <div className="mobile-landing-button-arrow">›</div>
          </button>
        ))}
      </div>
    </div>
  );
};

export default MobileLanding;
