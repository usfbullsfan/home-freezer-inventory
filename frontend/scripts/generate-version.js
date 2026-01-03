#!/usr/bin/env node

/**
 * Generate version information for the application
 * Creates public/version.json with version, commit hash, and build info
 */

import { execSync } from 'child_process';
import { readFileSync, writeFileSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Read version from package.json
const packageJsonPath = join(__dirname, '..', 'package.json');
const packageJson = JSON.parse(readFileSync(packageJsonPath, 'utf-8'));
const version = packageJson.version;

// Get git commit info
let commitHash = 'unknown';
let commitShort = 'unknown';
let branch = 'unknown';

try {
  commitHash = execSync('git rev-parse HEAD', { encoding: 'utf-8' }).trim();
  commitShort = execSync('git rev-parse --short HEAD', { encoding: 'utf-8' }).trim();
  branch = execSync('git rev-parse --abbrev-ref HEAD', { encoding: 'utf-8' }).trim();
} catch (error) {
  console.warn('Warning: Could not get git information');
}

// Build version info
const versionInfo = {
  version: version,
  commit: commitHash,
  commitShort: commitShort,
  branch: branch,
  buildDate: new Date().toISOString(),
};

// Detect environment (check if dev branch or dev environment variable)
const isDev = branch.includes('dev') ||
              process.env.NODE_ENV === 'development' ||
              process.env.VITE_DEV === 'true';

// Generate PWA manifest based on environment
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

// Write to public directory
const publicDir = join(__dirname, '..', 'public');

try {
  mkdirSync(publicDir, { recursive: true });

  // Write version.json
  const versionPath = join(publicDir, 'version.json');
  writeFileSync(versionPath, JSON.stringify(versionInfo, null, 2));

  // Write manifest.json
  const manifestPath = join(publicDir, 'manifest.json');
  writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));

  console.log('✓ Generated version.json');
  console.log(`  Version: ${version}`);
  console.log(`  Commit: ${commitShort}`);
  console.log(`  Branch: ${branch}`);
  console.log('✓ Generated manifest.json');
  console.log(`  Environment: ${isDev ? 'Development' : 'Production'}`);
  console.log(`  App Name: ${manifest.short_name}`);
} catch (error) {
  console.error('Error writing files:', error);
  process.exit(1);
}
