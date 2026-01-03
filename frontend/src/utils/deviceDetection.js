/**
 * Device detection utilities for mobile-first design
 */

/**
 * Check if the current device is mobile based on screen width and user agent
 * @returns {boolean} True if mobile device
 */
export const isMobileDevice = () => {
  // Check screen width (768px is the standard mobile breakpoint)
  const isMobileWidth = window.innerWidth <= 768;

  // Check user agent for mobile devices
  const userAgent = navigator.userAgent || navigator.vendor || window.opera;
  const isMobileUA = /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(userAgent.toLowerCase());

  // Device is considered mobile if either condition is true
  return isMobileWidth || isMobileUA;
};

/**
 * Check if user requested desktop site (browser setting)
 * @returns {boolean} True if desktop site requested
 */
export const isDesktopSiteRequested = () => {
  // Check if the browser is requesting desktop site
  // This is a heuristic - desktop mode on mobile typically has larger width
  const userAgent = navigator.userAgent || navigator.vendor || window.opera;
  const isMobileUA = /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(userAgent.toLowerCase());

  // If mobile UA but width > 1024, user probably requested desktop site
  if (isMobileUA && window.innerWidth > 1024) {
    return true;
  }

  return false;
};

/**
 * Check if we're in dev environment
 * @returns {boolean} True if dev environment
 */
export const isDevEnvironment = () => {
  const hostname = window.location.hostname;
  return hostname === 'dev.thefreezer.xyz' || hostname === 'localhost' || hostname === '127.0.0.1';
};

/**
 * Get the appropriate app name based on environment
 * @returns {string} App name
 */
export const getAppName = () => {
  return isDevEnvironment() ? 'Freezer App - Dev' : 'Freezer App';
};

/**
 * Get the appropriate logo path based on environment
 * @returns {string} Logo path
 */
export const getLogoPath = () => {
  return isDevEnvironment() ? '/logo-dev-192.png' : '/logo-192.png';
};

/**
 * Check if device is in standalone mode (installed as PWA)
 * @returns {boolean} True if running as PWA
 */
export const isStandaloneMode = () => {
  return window.matchMedia('(display-mode: standalone)').matches ||
         window.navigator.standalone === true;
};

/**
 * Check if PWA installation is supported
 * @returns {boolean} True if PWA install is supported
 */
export const isPWAInstallSupported = () => {
  return 'serviceWorker' in navigator && 'BeforeInstallPromptEvent' in window;
};
