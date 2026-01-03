import { useState, useEffect } from 'react';
import { isStandaloneMode, getAppName, getLogoPath } from '../utils/deviceDetection';
import api from '../services/api';
import './InstallPrompt.css';

/**
 * Install Prompt Component
 * Shows an overlay prompting users to install the app to their home screen
 * Only shows once per user and can be permanently dismissed
 */
const InstallPrompt = () => {
  const [showPrompt, setShowPrompt] = useState(false);
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [isIOS, setIsIOS] = useState(false);

  useEffect(() => {
    // Don't show if already installed
    if (isStandaloneMode()) {
      return;
    }

    // Check if user has dismissed the prompt before
    checkIfDismissed();

    // Detect iOS
    const iOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    setIsIOS(iOS);

    // Listen for beforeinstallprompt event (Chrome, Edge, etc.)
    const handleBeforeInstallPrompt = (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    };
  }, []);

  const checkIfDismissed = async () => {
    try {
      const response = await api.get('/api/settings/user');
      const settings = response.data;

      // Find the install_prompt_dismissed setting
      const dismissed = settings.find(s => s.setting_name === 'install_prompt_dismissed');

      if (!dismissed || dismissed.setting_value === 'false') {
        // Show prompt after a short delay (give user time to orient)
        setTimeout(() => setShowPrompt(true), 3000);
      }
    } catch (error) {
      console.error('Error checking install prompt status:', error);
      // Show prompt anyway if we can't check
      setTimeout(() => setShowPrompt(true), 3000);
    }
  };

  const handleInstallClick = async () => {
    if (deferredPrompt) {
      // Show the install prompt
      deferredPrompt.prompt();

      // Wait for the user's response
      const { outcome } = await deferredPrompt.userChoice;

      if (outcome === 'accepted') {
        console.log('User accepted the install prompt');
      }

      // Clear the deferred prompt
      setDeferredPrompt(null);
    }

    // Close the prompt
    handleClose();
  };

  const handleClose = async () => {
    setShowPrompt(false);

    // Mark as dismissed in the database
    try {
      await api.post('/api/settings/user', {
        setting_name: 'install_prompt_dismissed',
        setting_value: 'true'
      });
    } catch (error) {
      console.error('Error saving install prompt dismissal:', error);
    }
  };

  if (!showPrompt) {
    return null;
  }

  return (
    <div className="install-prompt-overlay">
      <div className="install-prompt-modal">
        <button className="install-prompt-close" onClick={handleClose}>
          ×
        </button>

        <div className="install-prompt-content">
          <img
            src={getLogoPath()}
            alt="Freezer App Logo"
            className="install-prompt-logo"
          />

          <h2 className="install-prompt-title">Install {getAppName()}</h2>

          <p className="install-prompt-description">
            Add this app to your home screen for quick and easy access when you're on the go.
          </p>

          {isIOS ? (
            // iOS instructions
            <div className="install-prompt-instructions">
              <p>To install this app:</p>
              <ol>
                <li>Tap the Share button <span className="ios-share-icon">⎙</span></li>
                <li>Scroll down and tap "Add to Home Screen"</li>
                <li>Tap "Add" in the top right corner</li>
              </ol>
            </div>
          ) : (
            // Android/Chrome instructions
            <div className="install-prompt-actions">
              {deferredPrompt ? (
                <button
                  className="install-prompt-button install-prompt-button-primary"
                  onClick={handleInstallClick}
                >
                  Install App
                </button>
              ) : (
                <div className="install-prompt-instructions">
                  <p>To install this app:</p>
                  <ol>
                    <li>Tap the menu icon (⋮) in your browser</li>
                    <li>Tap "Install app" or "Add to Home screen"</li>
                  </ol>
                </div>
              )}
            </div>
          )}

          <button
            className="install-prompt-button install-prompt-button-secondary"
            onClick={handleClose}
          >
            Maybe Later
          </button>
        </div>
      </div>
    </div>
  );
};

export default InstallPrompt;
