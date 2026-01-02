import { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

/**
 * QRRedirect - Handles QR code scans and redirects to inventory
 *
 * When a QR code is scanned, this component:
 * 1. Extracts the QR code from the URL
 * 2. Redirects to inventory with the QR code as a search parameter
 * 3. The Inventory page will auto-search and show the item
 */
function QRRedirect() {
  const { qrCode } = useParams();
  const navigate = useNavigate();

  useEffect(() => {
    if (qrCode) {
      // Redirect to inventory with the QR code as search parameter
      navigate(`/?qr=${qrCode}`);
    } else {
      // No QR code provided, just go to inventory
      navigate('/');
    }
  }, [qrCode, navigate]);

  return (
    <div className="container" style={{ textAlign: 'center', marginTop: '2rem' }}>
      <h2>Loading item...</h2>
      <p>Redirecting to inventory...</p>
    </div>
  );
}

export default QRRedirect;
