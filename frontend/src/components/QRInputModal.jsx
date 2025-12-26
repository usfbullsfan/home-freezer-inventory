import { useState } from 'react';

function QRInputModal({ onClose, onSubmit }) {
  const [qrCode, setQrCode] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (qrCode.trim()) {
      // Handle both direct QR codes and URL-encoded ones (freezer-item:CODE)
      const code = qrCode.includes(':') ? qrCode.split(':')[1] : qrCode;
      onSubmit(code.trim());
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>Enter QR Code</h2>

        <p style={{ marginBottom: '1rem', color: '#7f8c8d' }}>
          Enter the QR code manually or paste it from a scanner.
          In a future version, you'll be able to scan directly with your camera.
        </p>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="qr_code">QR Code / Barcode</label>
            <input
              type="text"
              id="qr_code"
              value={qrCode}
              onChange={(e) => setQrCode(e.target.value)}
              placeholder="e.g., FRZ-ABC123DEF456"
              autoFocus
              required
            />
            <small style={{ color: '#7f8c8d' }}>
              Enter the code printed on your item's label
            </small>
          </div>

          <div className="modal-actions">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onClose}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
            >
              Look Up Item
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default QRInputModal;
