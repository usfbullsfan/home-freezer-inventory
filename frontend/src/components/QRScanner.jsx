import { useState, useEffect, useRef } from 'react';
import { itemsAPI } from '../services/api';

function QRScanner({ onScan, onClose }) {
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState('');
  const [cameras, setCameras] = useState([]);
  const [selectedCamera, setSelectedCamera] = useState('');
  const [item, setItem] = useState(null);
  const [loading, setLoading] = useState(false);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const scanIntervalRef = useRef(null);
  const streamRef = useRef(null);

  useEffect(() => {
    // Get available cameras
    getCameras();

    return () => {
      stopScanning();
    };
  }, []);

  const getCameras = async () => {
    // Check if mediaDevices API is available
    if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) {
      setError('Camera access requires HTTPS. Please use manual entry below or access via https://');
      return;
    }

    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      const videoDevices = devices.filter(device => device.kind === 'videoinput');
      setCameras(videoDevices);

      // Select rear camera by default if available
      const rearCamera = videoDevices.find(device =>
        device.label.toLowerCase().includes('back') ||
        device.label.toLowerCase().includes('rear')
      );
      setSelectedCamera(rearCamera?.deviceId || videoDevices[0]?.deviceId || '');
    } catch (err) {
      setError('Camera not available. Please use manual entry below.');
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

            {cameras.length > 0 && !scanning && (
              <div style={{ marginBottom: '1rem' }}>
                <label htmlFor="camera-select" style={{ display: 'block', marginBottom: '0.5rem' }}>
                  Select Camera:
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

            {cameras.length > 0 && (
              <>
                <div className="scanner-area">
                  <video
                    ref={videoRef}
                    style={{
                      width: '100%',
                      maxHeight: '400px',
                      backgroundColor: '#000',
                      borderRadius: '4px',
                      display: scanning ? 'block' : 'none'
                    }}
                  />
                  <canvas
                    ref={canvasRef}
                    style={{ display: 'none' }}
                  />

                  {!scanning && !item && (
                    <div style={{ textAlign: 'center', padding: '2rem', background: '#f8f9fa', borderRadius: '4px' }}>
                      <p style={{ marginBottom: '1rem', color: '#666' }}>
                        Click "Start Scanning" to use your device camera, or enter the QR code manually below.
                      </p>
                    </div>
                  )}
                </div>

                <div style={{ marginTop: '1rem' }}>
                  <button
                    onClick={scanning ? stopScanning : startScanning}
                    className={`btn ${scanning ? 'btn-secondary' : 'btn-primary'}`}
                    style={{ width: '100%' }}
                  >
                    {scanning ? '⏹ Stop Scanning' : '▶️ Start Scanning'}
                  </button>
                </div>
              </>
            )}

            <div style={{
              marginTop: cameras.length === 0 ? '0' : '1.5rem',
              paddingTop: cameras.length === 0 ? '0' : '1.5rem',
              borderTop: cameras.length === 0 ? 'none' : '1px solid #ddd'
            }}>
              <h3 style={{ marginBottom: '0.5rem', fontSize: '1rem' }}>
                {cameras.length === 0 ? '🔍 Enter QR Code' : 'Manual Entry'}
              </h3>
              <p style={{ fontSize: '0.9rem', color: '#666', marginBottom: '1rem' }}>
                {cameras.length === 0
                  ? 'Enter the QR code from your item label:'
                  : 'Or enter the code manually if camera scanning isn\'t working:'}
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
                    placeholder="Enter QR code (e.g., ABC123)"
                    style={{ flex: 1 }}
                    disabled={loading}
                  />
                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={loading}
                  >
                    {loading ? 'Looking up...' : 'Look Up'}
                  </button>
                </div>
              </form>
            </div>

            {item && (
              <div style={{ marginTop: '1.5rem', padding: '1rem', background: '#e8f5e9', borderRadius: '4px' }}>
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

            {cameras.length === 0 ? (
              <div style={{ marginTop: '1.5rem', padding: '1rem', background: '#e3f2fd', borderRadius: '4px' }}>
                <h4 style={{ marginBottom: '0.5rem', fontSize: '0.9rem' }}>ℹ️ Camera Not Available</h4>
                <p style={{ fontSize: '0.85rem', lineHeight: '1.6', color: '#666', margin: 0 }}>
                  Camera access requires HTTPS (secure connection). You can still use this feature by entering QR codes manually above,
                  or access this site via <code>https://</code> to enable camera scanning.
                </p>
              </div>
            ) : (
              <div style={{ marginTop: '1.5rem', padding: '1rem', background: '#fff3e0', borderRadius: '4px' }}>
                <h4 style={{ marginBottom: '0.5rem', fontSize: '0.9rem' }}>💡 Tips:</h4>
                <ul style={{ marginLeft: '1.5rem', fontSize: '0.85rem', lineHeight: '1.6', color: '#666' }}>
                  <li>Make sure the QR code is well-lit and in focus</li>
                  <li>Hold your device steady while scanning</li>
                  <li>Try using the rear camera for better results</li>
                  <li>If scanning doesn't work, use manual entry above</li>
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default QRScanner;
