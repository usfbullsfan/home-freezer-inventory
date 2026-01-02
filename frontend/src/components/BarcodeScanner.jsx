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

      // Wait a bit for the DOM to be ready
      await new Promise(resolve => setTimeout(resolve, 100));

      if (!scannerRef.current) {
        setError('Scanner not ready. Please try again.');
        return;
      }

      await Quagga.init(
        {
          inputStream: {
            type: 'LiveStream',
            target: scannerRef.current,
            constraints: {
              facingMode: 'environment',
              width: { min: 640, ideal: 1280, max: 1920 },
              height: { min: 480, ideal: 720, max: 1080 }
            }
          },
          locator: {
            patchSize: 'large',
            halfSample: true
          },
          numOfWorkers: navigator.hardwareConcurrency || 2,
          frequency: 10,
          decoder: {
            readers: [
              'upc_reader',
              'upc_e_reader',
              'ean_reader',
              'ean_8_reader',
              'code_128_reader',
              'code_39_reader'
            ],
            multiple: false
          },
          locate: true
        },
        (err) => {
          if (err) {
            console.error('Quagga initialization error:', err);
            setError('Failed to start camera. Please ensure you have granted camera permissions and try again.');
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
      setError('Failed to start barcode scanner: ' + err.message);
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
        <h2 style={{ color: 'white', margin: 0, fontSize: '1.2rem' }}>📊 Scan Barcode</h2>
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

      {/* Scanner area */}
      <div
        ref={scannerRef}
        id="barcode-scanner"
        style={{
          flex: 1,
          width: '100%',
          height: '100%',
          position: 'relative',
          overflow: 'hidden'
        }}
      />

      {/* Scanning guide overlay */}
      {scanning && !detected && (
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: '85%',
          maxWidth: '400px',
          height: '180px',
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
            Align barcode here
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

      {detected && (
        <div style={{
          position: 'absolute',
          bottom: '2rem',
          left: '1rem',
          right: '1rem',
          background: 'rgba(232, 245, 233, 0.95)',
          color: '#2e7d32',
          padding: '1rem',
          borderRadius: '8px',
          border: '2px solid #4caf50',
          textAlign: 'center',
          fontSize: '1.1rem',
          fontWeight: '500',
          zIndex: 10
        }}>
          ✓ Detected: {detected}
        </div>
      )}
    </div>
  );
}

export default BarcodeScanner;
