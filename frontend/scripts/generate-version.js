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

// Write to public/version.json
const publicDir = join(__dirname, '..', 'public');
const outputPath = join(publicDir, 'version.json');

try {
  mkdirSync(publicDir, { recursive: true });
  writeFileSync(outputPath, JSON.stringify(versionInfo, null, 2));
  console.log('✓ Generated version.json');
  console.log(`  Version: ${version}`);
  console.log(`  Commit: ${commitShort}`);
  console.log(`  Branch: ${branch}`);
} catch (error) {
  console.error('Error writing version.json:', error);
  process.exit(1);
}
