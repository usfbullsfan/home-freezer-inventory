import { useState, useEffect, useRef } from 'react';
import Quagga from '@ericblade/quagga2';

function BarcodeScanner({ onScan, onClose }) {
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState('');
  const [detected, setDetected] = useState('');
  const scannerRef = useRef(null);

  useEffect(() => {
    // Auto-start scanner when component mounts
    startScanning();

    return () => {
      stopScanning();
    };
  }, []);

  const startScanning = async () => {
    try {
      setError('');
      setDetected('');

      await Quagga.init(
        {
          inputStream: {
            type: 'LiveStream',
            target: scannerRef.current,
            constraints: {
              facingMode: 'environment',
              width: { ideal: 1920 },
              height: { ideal: 1080 }
            },
            area: {
              top: '25%',
              right: '5%',
              left: '5%',
              bottom: '25%'
            }
          },
          locator: {
            patchSize: 'large',
            halfSample: false
          },
          numOfWorkers: 4,
          frequency: 10,
          decoder: {
            readers: [
              'upc_reader',
              'upc_e_reader',
              'ean_reader',
              'ean_8_reader',
              'code_128_reader',
              'code_39_reader'
            ]
          },
          locate: true
        },
        (err) => {
          if (err) {
            console.error('Quagga initialization error:', err);
            setError('Failed to start camera: ' + err.message + '. Please ensure you have granted camera permissions.');
            return;
          }

          Quagga.start();
          setScanning(true);
        }
      );

      // Listen for barcode detections
      Quagga.onDetected(handleDetected);
    } catch (err) {
      console.error('Scanner error:', err);
      setError('Failed to start barcode scanner. Please try again.');
    }
  };

  const stopScanning = () => {
    if (scanning) {
      Quagga.stop();
      Quagga.offDetected(handleDetected);
      setScanning(false);
    }
  };

  const handleDetected = (result) => {
    if (result && result.codeResult && result.codeResult.code) {
      const code = result.codeResult.code;
      const format = result.codeResult.format;

      // Filter for high-confidence reads
      if (result.codeResult.startInfo && result.codeResult.startInfo.error < 0.1) {
        setDetected(`${format}: ${code}`);

        // Stop scanning to prevent multiple detections
        stopScanning();

        // Call the callback with the detected code
        if (onScan) {
          onScan(code);
        }
      }
    }
  };

  return (
    <div className="qr-scanner-modal">
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal qr-scanner-container" onClick={(e) => e.stopPropagation()}>
          <div className="modal-header">
            <h2>📊 Scan Barcode</h2>
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

            {detected && (
              <div style={{
                background: '#e8f5e9',
                color: '#2e7d32',
                padding: '1rem',
                borderRadius: '4px',
                marginBottom: '1rem',
                border: '1px solid #4caf50',
                textAlign: 'center'
              }}>
                ✓ Detected: {detected}
              </div>
            )}

            {!detected && (
              <>
                <p style={{ fontSize: '0.9rem', color: '#666', marginBottom: '1rem', textAlign: 'center' }}>
                  Point your camera at a barcode (UPC, EAN, etc.)
                </p>

                <div className="scanner-area" style={{ position: 'relative' }}>
                  <div
                    ref={scannerRef}
                    style={{
                      width: '100%',
                      minHeight: '500px',
                      backgroundColor: '#000',
                      borderRadius: '4px',
                      overflow: 'hidden',
                      position: 'relative'
                    }}
                  />

                  {/* Scanning guide overlay - larger area for easier alignment */}
                  {scanning && (
                    <div style={{
                      position: 'absolute',
                      top: '50%',
                      left: '50%',
                      transform: 'translate(-50%, -50%)',
                      width: '90%',
                      height: '200px',
                      border: '3px solid #4caf50',
                      borderRadius: '8px',
                      pointerEvents: 'none',
                      boxShadow: '0 0 0 9999px rgba(0,0,0,0.4)'
                    }}>
                      <div style={{
                        position: 'absolute',
                        top: '-35px',
                        left: '50%',
                        transform: 'translateX(-50%)',
                        background: 'rgba(76, 175, 80, 0.95)',
                        color: 'white',
                        padding: '0.4rem 0.75rem',
                        borderRadius: '6px',
                        fontSize: '0.9rem',
                        fontWeight: '500',
                        whiteSpace: 'nowrap',
                        boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
                      }}>
                        Align barcode in this area
                      </div>
                    </div>
                  )}
                </div>

                {scanning && (
                  <div style={{ marginTop: '1rem', textAlign: 'center' }}>
                    <p style={{ fontSize: '0.85rem', color: '#666' }}>
                      📸 Camera is active - position barcode in the guide
                    </p>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default BarcodeScanner;
