/**
 * Dynamically update PWA manifest based on environment
 * This runs on app startup to set the correct app name and icons
 */

export const updateManifest = () => {
  const isDev = window.location.hostname === 'dev.thefreezer.xyz' ||
                window.location.hostname === 'localhost' ||
                window.location.hostname === '127.0.0.1';

  const manifest = {
    name: isDev ? 'Freezer App - Dev' : 'Freezer App',
    short_name: isDev ? 'Freezer App - Dev' : 'Freezer App',
    description: 'Track and manage your freezer inventory',
    start_url: '/',
    display: 'standalone',
    background_color: '#ffffff',
    theme_color: isDev ? '#f39c12' : '#1976d2',
    orientation: 'portrait-primary',
    icons: [
      {
        src: isDev ? '/logo-dev-192.png' : '/logo-192.png',
        sizes: '192x192',
        type: 'image/png',
        purpose: 'any maskable'
      },
      {
        src: isDev ? '/logo-dev-512.png' : '/logo-512.png',
        sizes: '512x512',
        type: 'image/png',
        purpose: 'any maskable'
      }
    ]
  };

  // Create a blob URL for the manifest
  const manifestBlob = new Blob([JSON.stringify(manifest)], { type: 'application/json' });
  const manifestURL = URL.createObjectURL(manifestBlob);

  // Update the manifest link
  const manifestLink = document.querySelector('link[rel="manifest"]');
  if (manifestLink) {
    manifestLink.href = manifestURL;
  }

  // Update the apple-mobile-web-app-title
  let appleTitle = document.querySelector('meta[name="apple-mobile-web-app-title"]');
  if (!appleTitle) {
    appleTitle = document.createElement('meta');
    appleTitle.setAttribute('name', 'apple-mobile-web-app-title');
    document.head.appendChild(appleTitle);
  }
  appleTitle.setAttribute('content', manifest.name);

  // Update theme color
  const themeColor = document.querySelector('meta[name="theme-color"]');
  if (themeColor) {
    themeColor.setAttribute('content', manifest.theme_color);
  }

  // Update favicon and apple touch icon
  const favicon = document.querySelector('link[rel="icon"]');
  if (favicon) {
    favicon.href = isDev ? '/logo-dev-192.png' : '/logo-192.png';
  }

  const appleTouchIcon = document.querySelector('link[rel="apple-touch-icon"]');
  if (appleTouchIcon) {
    appleTouchIcon.href = isDev ? '/logo-dev-192.png' : '/logo-192.png';
  }
};
