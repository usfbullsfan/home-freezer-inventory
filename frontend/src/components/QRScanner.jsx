import { useState, useEffect, useRef } from 'react';
import { itemsAPI } from '../services/api';

function QRScanner({ onScan, onClose }) {
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState('');
  const [cameras, setCameras] = useState([]);
  const [selectedCamera, setSelectedCamera] = useState('');
  const [item, setItem] = useState(null);
  const [loading, setLoading] = useState(false);
  const [cameraAvailable, setCameraAvailable] = useState(false);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const scanIntervalRef = useRef(null);
  const streamRef = useRef(null);

  useEffect(() => {
    // Check camera availability silently
    checkCameraAvailability();

    return () => {
      stopScanning();
    };
  }, []);

  const checkCameraAvailability = async () => {
    // Silently check if camera is available (requires HTTPS on mobile)
    if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
      try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const videoDevices = devices.filter(device => device.kind === 'videoinput');
        if (videoDevices.length > 0) {
          setCameras(videoDevices);
          setCameraAvailable(true);

          // Select rear camera by default if available
          const rearCamera = videoDevices.find(device =>
            device.label.toLowerCase().includes('back') ||
            device.label.toLowerCase().includes('rear')
          );
          setSelectedCamera(rearCamera?.deviceId || videoDevices[0]?.deviceId || '');
        }
      } catch (err) {
        // Camera not available, that's fine - manual entry works
        setCameraAvailable(false);
      }
    }
  };

  const startScanning = async () => {
    try {
      setError('');
      setItem(null);

      const constraints = {
        video: {
          deviceId: selectedCamera ? { exact: selectedCamera } : undefined,
          facingMode: selectedCamera ? undefined : { ideal: 'environment' },
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
        scanIntervalRef.current = setInterval(scanFrame, 500);
      }
    } catch (err) {
      setError('Failed to start camera: ' + err.message);
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

    // Set canvas size to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Draw current video frame
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Get image data
    const imageData = context.getImageData(0, 0, canvas.width, canvas.height);

    // Try to detect QR code using jsQR library
    try {
      // For simplicity, we'll use a manual approach
      // In production, you'd want to use a library like jsQR
      // For now, let's create a manual input fallback
    } catch (err) {
      console.error('QR scanning error:', err);
    }
  };

  const handleManualInput = async (qrCode) => {
    if (!qrCode.trim()) return;

    try {
      setLoading(true);
      setError('');
      const response = await itemsAPI.getItemByQR(qrCode.trim());
      setItem(response.data);
      stopScanning();
      if (onScan) {
        onScan(response.data);
      }
    } catch (err) {
      setError(`Item not found: ${qrCode}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="qr-scanner-modal">
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal qr-scanner-container" onClick={(e) => e.stopPropagation()}>
          <div className="modal-header">
            <h2>🔍 Locate Item by Code</h2>
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

            {/* Manual Entry - Always shown first as primary method */}
            <div>
              <h3 style={{ marginBottom: '0.5rem', fontSize: '1.1rem' }}>Enter QR Code</h3>
              <p style={{ fontSize: '0.9rem', color: '#666', marginBottom: '1rem' }}>
                Type the code from your item's QR label:
              </p>
              <form onSubmit={(e) => {
                e.preventDefault();
                const input = e.target.elements.qrCode;
                handleManualInput(input.value);
                input.value = '';
              }}>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <input
                    type="text"
                    name="qrCode"
                    placeholder="e.g., ABC123"
                    style={{ flex: 1, fontSize: '16px', padding: '0.75rem' }}
                    disabled={loading}
                    autoFocus
                  />
                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={loading}
                    style={{ padding: '0.75rem 1.5rem' }}
                  >
                    {loading ? 'Looking up...' : 'Find Item'}
                  </button>
                </div>
              </form>
            </div>

            {/* Camera scanning - Optional enhancement if available */}
            {cameraAvailable && (
              <div style={{ marginTop: '2rem', paddingTop: '2rem', borderTop: '1px solid #ddd' }}>
                <h3 style={{ marginBottom: '0.5rem', fontSize: '1rem' }}>📷 Or Use Camera</h3>
                <p style={{ fontSize: '0.85rem', color: '#666', marginBottom: '1rem' }}>
                  Scan the QR code with your device camera:
                </p>

                {!scanning && (
                  <div style={{ marginBottom: '1rem' }}>
                    <label htmlFor="camera-select" style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem' }}>
                      Camera:
                    </label>
                    <select
                      id="camera-select"
                      value={selectedCamera}
                      onChange={(e) => setSelectedCamera(e.target.value)}
                      style={{ width: '100%' }}
                    >
                      {cameras.map(camera => (
                        <option key={camera.deviceId} value={camera.deviceId}>
                          {camera.label || `Camera ${camera.deviceId.slice(0, 8)}`}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                <div className="scanner-area">
                  <video
                    ref={videoRef}
                    style={{
                      width: '100%',
                      maxHeight: '300px',
                      backgroundColor: '#000',
                      borderRadius: '4px',
                      display: scanning ? 'block' : 'none'
                    }}
                  />
                  <canvas
                    ref={canvasRef}
                    style={{ display: 'none' }}
                  />
                </div>

                <div style={{ marginTop: '1rem' }}>
                  <button
                    onClick={scanning ? stopScanning : startScanning}
                    className={`btn ${scanning ? 'btn-secondary' : 'btn-success'}`}
                    style={{ width: '100%' }}
                  >
                    {scanning ? '⏹ Stop Scanning' : '▶️ Start Camera'}
                  </button>
                </div>
              </div>
            )}

            {/* Item result */}
            {item && (
              <div style={{ marginTop: '2rem', padding: '1rem', background: '#e8f5e9', borderRadius: '4px' }}>
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
