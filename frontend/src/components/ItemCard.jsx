import { useState } from 'react';
import { itemsAPI } from '../services/api';

function ItemCard({ item, onEdit, onStatusChange }) {
  const [showQR, setShowQR] = useState(false);

  const getStatusClass = () => {
    return `status-badge status-${item.status}`;
  };

  const getCardClass = () => {
    let classes = 'item-card';

    if (item.status === 'in_freezer' && item.expiration_date) {
      const daysUntilExpiry = Math.floor(
        (new Date(item.expiration_date) - new Date()) / (1000 * 60 * 60 * 24)
      );

      if (daysUntilExpiry < 0) {
        classes += ' expired';
      } else if (daysUntilExpiry <= 30) {
        classes += ' expiring-soon';
      }

      // Check if it's one of the oldest (older than 6 months)
      const daysInFreezer = Math.floor(
        (new Date() - new Date(item.added_date)) / (1000 * 60 * 60 * 24)
      );
      if (daysInFreezer > 180) {
        classes += ' oldest';
      }
    }

    return classes;
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };

  const getDaysInFreezer = () => {
    return Math.floor(
      (new Date() - new Date(item.added_date)) / (1000 * 60 * 60 * 24)
    );
  };

  const getDaysUntilExpiry = () => {
    if (!item.expiration_date) return null;
    return Math.floor(
      (new Date(item.expiration_date) - new Date()) / (1000 * 60 * 60 * 24)
    );
  };

  return (
    <div className={getCardClass()}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
        <h3>{item.name}</h3>
        <span className={getStatusClass()}>
          {item.status.replace('_', ' ')}
        </span>
      </div>

      <div className="item-meta">
        {item.category_name && `${item.category_name} • `}
        Added {formatDate(item.added_date)}
        {item.added_by_username && ` by ${item.added_by_username}`}
      </div>

      <div className="item-details">
        {item.source && (
          <p>
            <strong>Source:</strong>
            <span>{item.source}</span>
          </p>
        )}
        {item.weight && (
          <p>
            <strong>Weight:</strong>
            <span>{item.weight} {item.weight_unit}</span>
          </p>
        )}
        <p>
          <strong>Days in freezer:</strong>
          <span>{getDaysInFreezer()} days</span>
        </p>
        {item.expiration_date && (
          <p>
            <strong>Expires:</strong>
            <span>
              {formatDate(item.expiration_date)}
              {getDaysUntilExpiry() !== null && (
                <> ({getDaysUntilExpiry() >= 0 ? `${getDaysUntilExpiry()} days` : 'EXPIRED'})</>
              )}
            </span>
          </p>
        )}
        {item.removed_date && (
          <p>
            <strong>Removed:</strong>
            <span>{formatDate(item.removed_date)}</span>
          </p>
        )}
        {item.notes && (
          <p style={{ gridColumn: '1 / -1', marginTop: '0.5rem' }}>
            <strong>Notes:</strong> {item.notes}
          </p>
        )}
      </div>

      <div className="item-actions">
        <button
          className="btn btn-secondary"
          onClick={() => setShowQR(!showQR)}
          style={{ flex: 0.5 }}
        >
          QR
        </button>
        <button
          className="btn btn-primary"
          onClick={onEdit}
        >
          Edit
        </button>
        {item.status === 'in_freezer' && (
          <>
            <button
              className="btn btn-success"
              onClick={() => onStatusChange('consumed')}
            >
              Consumed
            </button>
            <button
              className="btn btn-danger"
              onClick={() => onStatusChange('thrown_out')}
            >
              Discard
            </button>
          </>
        )}
        {item.status !== 'in_freezer' && (
          <button
            className="btn btn-secondary"
            onClick={() => onStatusChange('in_freezer')}
          >
            Return to Freezer
          </button>
        )}
      </div>

      {showQR && (
        <div className="qr-code-display">
          <p style={{ marginBottom: '0.5rem', fontWeight: 'bold' }}>
            {item.qr_code}
          </p>
          <img
            src={itemsAPI.getQRImage(item.qr_code)}
            alt={`QR Code for ${item.name}`}
          />
          <p style={{ marginTop: '0.5rem', fontSize: '0.875rem', color: '#7f8c8d' }}>
            Scan this code to quickly access this item
          </p>
        </div>
      )}
    </div>
  );
}

export default ItemCard;
