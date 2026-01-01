import { useState } from 'react';
import { itemsAPI } from '../services/api';
import { formatLocalDate, daysBetween } from '../utils/dateUtils';

function ItemCard({ item, onEdit, onStatusChange }) {
  const [showQR, setShowQR] = useState(false);

  const getStatusClass = () => {
    return `status-badge status-${item.status}`;
  };

  const getCardClass = () => {
    let classes = 'item-card';

    if (item.status === 'in_freezer' && item.expiration_date) {
      const daysUntilExpiry = -daysBetween(item.expiration_date);

      if (daysUntilExpiry < 0) {
        classes += ' expired';
      } else if (daysUntilExpiry <= 30) {
        classes += ' expiring-soon';
      }

      // Check if it's one of the oldest (older than 6 months)
      const daysInFreezer = Math.max(0, daysBetween(item.added_date));
      if (daysInFreezer > 180) {
        classes += ' oldest';
      }
    }

    return classes;
  };

  const getDaysInFreezer = () => {
    return Math.max(0, daysBetween(item.added_date));
  };

  const getDaysUntilExpiry = () => {
    if (!item.expiration_date) return null;
    return -daysBetween(item.expiration_date);
  };

  return (
    <div className={getCardClass()}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', gap: '1rem' }}>
        {item.image_url && (
          <img
            src={item.image_url}
            alt={item.name}
            style={{
              width: '60px',
              height: '60px',
              objectFit: 'cover',
              borderRadius: '8px',
              flexShrink: 0
            }}
            onError={(e) => {
              e.target.style.display = 'none';
            }}
          />
        )}
        <div style={{ flex: 1, minWidth: 0 }}>
          <h3 style={{ margin: 0, marginBottom: '0.25rem' }}>{item.name}</h3>
        </div>
        <span className={getStatusClass()}>
          {item.status.replace('_', ' ')}
        </span>
      </div>

      <div className="item-meta">
        {item.category_name && `${item.category_name} • `}
        Added {formatLocalDate(item.added_date)}
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
            <strong>Size:</strong>
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
              {formatLocalDate(item.expiration_date)}
              {getDaysUntilExpiry() !== null && (
                <> ({getDaysUntilExpiry() >= 0 ? `${getDaysUntilExpiry()} days` : 'EXPIRED'})</>
              )}
            </span>
          </p>
        )}
        {item.removed_date && (
          <p>
            <strong>Removed:</strong>
            <span>{formatLocalDate(item.removed_date)}</span>
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
          Code
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
            Write this code on your bag or scan the QR code to quickly access this item
          </p>
        </div>
      )}
    </div>
  );
}

export default ItemCard;
