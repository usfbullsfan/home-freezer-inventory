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

  // Full-page scanner (better for mobile)
  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: '#000',
      zIndex: 9999,
      display: 'flex',
      flexDirection: 'column'
    }}>
      {/* Header */}
      <div style={{
        background: 'linear-gradient(to bottom, rgba(0,0,0,0.8), transparent)',
        padding: '1rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 10
      }}>
        <h2 style={{ color: 'white', margin: 0, fontSize: '1.2rem' }}>📷 Scan QR Code</h2>
        <button
          onClick={onClose}
          style={{
            background: 'rgba(255,255,255,0.2)',
            border: 'none',
            color: 'white',
            fontSize: '2rem',
            width: '40px',
            height: '40px',
            borderRadius: '50%',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 0
          }}
        >
          ×
        </button>
      </div>

      {/* Camera area */}
      <video
        ref={videoRef}
        autoPlay
        playsInline
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          position: 'absolute',
          top: 0,
          left: 0
        }}
      />
      <canvas
        ref={canvasRef}
        style={{ display: 'none' }}
      />

      {/* Scanning guide overlay - large square for QR codes */}
      {scanning && !item && !loading && (
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: '75%',
          maxWidth: '350px',
          aspectRatio: '1 / 1',
          border: '3px solid #4caf50',
          borderRadius: '12px',
          pointerEvents: 'none',
          boxShadow: '0 0 0 9999px rgba(0,0,0,0.5)'
        }}>
          <div style={{
            position: 'absolute',
            top: '-40px',
            left: '50%',
            transform: 'translateX(-50%)',
            background: 'rgba(76, 175, 80, 0.95)',
            color: 'white',
            padding: '0.5rem 1rem',
            borderRadius: '8px',
            fontSize: '0.95rem',
            fontWeight: '500',
            whiteSpace: 'nowrap',
            boxShadow: '0 2px 8px rgba(0,0,0,0.3)'
          }}>
            Align QR code here
          </div>
        </div>
      )}

      {/* Messages */}
      {error && (
        <div style={{
          position: 'absolute',
          bottom: '2rem',
          left: '1rem',
          right: '1rem',
          background: 'rgba(255, 243, 205, 0.95)',
          color: '#856404',
          padding: '1rem',
          borderRadius: '8px',
          border: '1px solid #ffeaa7',
          textAlign: 'center',
          zIndex: 10
        }}>
          ⚠️ {error}
        </div>
      )}

      {loading && (
        <div style={{
          position: 'absolute',
          bottom: '2rem',
          left: '1rem',
          right: '1rem',
          background: 'rgba(33, 150, 243, 0.95)',
          color: 'white',
          padding: '1rem',
          borderRadius: '8px',
          textAlign: 'center',
          fontSize: '1.1rem',
          fontWeight: '500',
          zIndex: 10
        }}>
          🔍 Looking up item...
        </div>
      )}

      {item && (
        <div style={{
          position: 'absolute',
          bottom: '2rem',
          left: '1rem',
          right: '1rem',
          background: 'rgba(232, 245, 233, 0.95)',
          color: '#2e7d32',
          padding: '1.25rem',
          borderRadius: '8px',
          border: '2px solid #4caf50',
          zIndex: 10
        }}>
          <h3 style={{ marginTop: 0, marginBottom: '0.75rem', color: '#2e7d32', fontSize: '1.2rem' }}>✓ Item Found!</h3>
          <div style={{ fontSize: '0.95rem' }}>
            <p style={{ margin: '0.5rem 0' }}><strong>Name:</strong> {item.name}</p>
            <p style={{ margin: '0.5rem 0' }}><strong>Category:</strong> {item.category_name || 'N/A'}</p>
            <p style={{ margin: '0.5rem 0' }}><strong>QR Code:</strong> <code>{item.qr_code}</code></p>
            {item.expiration_date && (
              <p style={{ margin: '0.5rem 0' }}><strong>Expires:</strong> {new Date(item.expiration_date).toLocaleDateString()}</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default QRScanner;
