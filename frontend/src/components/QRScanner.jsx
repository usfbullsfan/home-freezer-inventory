import { useState, useEffect, useRef } from 'react';
import jsQR from 'jsqr';
import { itemsAPI } from '../services/api';

function QRScanner({ onScan, onClose }) {
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState('');
  const [item, setItem] = useState(null);
  const [loading, setLoading] = useState(false);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const scanIntervalRef = useRef(null);
  const streamRef = useRef(null);

  useEffect(() => {
    // Auto-start camera when component mounts
    startScanning();

    return () => {
      stopScanning();
    };
  }, []);

  const startScanning = async () => {
    try {
      setError('');
      setItem(null);

      // Auto-select rear camera (environment-facing)
      const constraints = {
        video: {
          facingMode: { ideal: 'environment' },
          width: { ideal: 1280 },
          height: { ideal: 720 }
        }
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
        setScanning(true);

        // Start scanning loop
        scanIntervalRef.current = setInterval(scanFrame, 300);
      }
    } catch (err) {
      setError('Failed to start camera: ' + err.message + '. Please ensure you have granted camera permissions.');
    }
  };

  const stopScanning = () => {
    if (scanIntervalRef.current) {
      clearInterval(scanIntervalRef.current);
      scanIntervalRef.current = null;
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setScanning(false);
  };

  const scanFrame = () => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');

    // Ensure video is ready
    if (video.readyState !== video.HAVE_ENOUGH_DATA) return;

    // Set canvas size to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Draw current video frame
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Get image data
    const imageData = context.getImageData(0, 0, canvas.width, canvas.height);

    // Try to detect QR code using jsQR library
    try {
      const code = jsQR(imageData.data, imageData.width, imageData.height, {
        inversionAttempts: 'dontInvert',
      });

      if (code) {
        // QR code detected! Extract the item code from the URL
        const qrData = code.data;

        // The QR code contains a URL like "https://thefreezer.xyz/item/ABC123"
        // Extract the code from the URL
        const match = qrData.match(/\/item\/([A-Z0-9]+)/);
        if (match && match[1]) {
          const itemCode = match[1];
          handleQRCodeDetected(itemCode);
        } else {
          // Maybe it's just the code directly (for backwards compatibility)
          handleQRCodeDetected(qrData);
        }
      }
    } catch (err) {
      console.error('QR scanning error:', err);
    }
  };

  const handleQRCodeDetected = async (qrCode) => {
    if (!qrCode.trim()) return;

    // Stop scanning to prevent multiple detections
    stopScanning();

    try {
      setLoading(true);
      setError('');
      const response = await itemsAPI.getItemByQR(qrCode.trim());
      setItem(response.data);

      if (onScan) {
        onScan(response.data);
      }
    } catch (err) {
      setError(`Item not found: ${qrCode}`);
      // Restart scanning after a brief delay to allow user to read error
      setTimeout(() => {
        if (videoRef.current) {
          startScanning();
        }
      }, 2000);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="qr-scanner-modal">
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal qr-scanner-container" onClick={(e) => e.stopPropagation()}>
          <div className="modal-header">
            <h2>📷 Scan QR Code</h2>
            <button onClick={onClose} className="close-button">×</button>
          </div>

          <div className="modal-content">
            {error && (
              <div className="error-message" style={{
                background: '#fff3cd',
                color: '#856404',
                padding: '1rem',
                borderRadius: '4px',
                marginBottom: '1rem',
                border: '1px solid #ffeaa7'
              }}>
                ⚠️ {error}
              </div>
            )}

            {loading && (
              <div style={{ textAlign: 'center', padding: '1rem' }}>
                <p style={{ fontSize: '1.1rem', color: '#1976d2' }}>🔍 Looking up item...</p>
              </div>
            )}

            {!item && !loading && (
              <>
                <p style={{ fontSize: '0.9rem', color: '#666', marginBottom: '1rem', textAlign: 'center' }}>
                  Point your camera at a QR code to scan
                </p>

                <div className="scanner-area">
                  <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    style={{
                      width: '100%',
                      maxHeight: '400px',
                      backgroundColor: '#000',
                      borderRadius: '4px'
                    }}
                  />
                  <canvas
                    ref={canvasRef}
                    style={{ display: 'none' }}
                  />
                </div>

                {scanning && (
                  <div style={{ marginTop: '1rem', textAlign: 'center' }}>
                    <p style={{ fontSize: '0.85rem', color: '#666' }}>
                      📸 Camera is active - position QR code in view
                    </p>
                  </div>
                )}
              </>
            )}

            {/* Item result */}
            {item && (
              <div style={{ marginTop: '1rem', padding: '1rem', background: '#e8f5e9', borderRadius: '4px' }}>
                <h3 style={{ marginBottom: '0.5rem', color: '#2e7d32' }}>✓ Item Found!</h3>
                <div style={{ marginTop: '1rem' }}>
                  <p><strong>Name:</strong> {item.name}</p>
                  <p><strong>Category:</strong> {item.category_name || 'N/A'}</p>
                  <p><strong>QR Code:</strong> <code>{item.qr_code}</code></p>
                  {item.expiration_date && (
                    <p><strong>Expires:</strong> {new Date(item.expiration_date).toLocaleDateString()}</p>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default QRScanner;
