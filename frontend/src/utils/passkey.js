/**
 * Passkey Authentication Utilities
 * Simple wrapper around WebAuthn API
 */

import { startRegistration, startAuthentication } from '@simplewebauthn/browser';
import api from '../services/api';

/**
 * Register a new passkey for a user
 * @param {string} username - Username to register passkey for
 * @param {string} [name] - Optional friendly name for the passkey
 * @returns {Promise<{success: boolean, credentialId?: string, error?: string}>}
 */
export async function registerPasskey(username, name = null) {
  try {
    // Step 1: Get registration options from server
    const beginResponse = await api.post('/passkey/register/begin', { username });
    const { options, challengeId } = beginResponse.data;

    // Step 2: Prompt user to create passkey (Face ID, Windows Hello, etc.)
    const credential = await startRegistration(JSON.parse(options));

    // Step 3: Send credential to server for verification
    const completeResponse = await api.post('/passkey/register/complete', {
      credential,
      challengeId,
      name: name || 'Passkey'
    });

    return {
      success: true,
      credentialId: completeResponse.data.credentialId
    };
  } catch (error) {
    console.error('Passkey registration error:', error);
    return {
      success: false,
      error: error.response?.data?.error || error.message || 'Registration failed'
    };
  }
}

/**
 * Login with a passkey
 * @param {string} [username] - Optional username (for non-discoverable credentials)
 * @returns {Promise<{success: boolean, token?: string, user?: object, error?: string}>}
 */
export async function loginWithPasskey(username = null) {
  try {
    // Step 1: Get authentication options from server
    const beginResponse = await api.post('/passkey/login/begin', { username });
    const { options, challengeId } = beginResponse.data;

    // Step 2: Prompt user to authenticate (Face ID, Windows Hello, etc.)
    const credential = await startAuthentication(JSON.parse(options));

    // Step 3: Send assertion to server for verification
    const completeResponse = await api.post('/passkey/login/complete', {
      credential,
      challengeId
    });

    const { token, user } = completeResponse.data;

    // Store token and user info
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(user));

    return {
      success: true,
      token,
      user
    };
  } catch (error) {
    console.error('Passkey login error:', error);
    return {
      success: false,
      error: error.response?.data?.error || error.message || 'Login failed'
    };
  }
}

/**
 * Check if browser supports WebAuthn
 * @returns {boolean}
 */
export function supportsPasskeys() {
  return (
    window.PublicKeyCredential !== undefined &&
    typeof window.PublicKeyCredential === 'function'
  );
}

/**
 * Generate recovery codes for current user
 * @returns {Promise<{success: boolean, codes?: string[], error?: string}>}
 */
export async function generateRecoveryCodes() {
  try {
    const response = await api.post('/passkey/recovery/generate');
    return {
      success: true,
      codes: response.data.codes
    };
  } catch (error) {
    console.error('Recovery code generation error:', error);
    return {
      success: false,
      error: error.response?.data?.error || error.message || 'Failed to generate codes'
    };
  }
}

/**
 * Use a recovery code to get temporary access
 * @param {string} username - Username
 * @param {string} code - Recovery code
 * @returns {Promise<{success: boolean, token?: string, error?: string}>}
 */
export async function useRecoveryCode(username, code) {
  try {
    const response = await api.post('/passkey/recovery/use', { username, code });
    const { temporaryToken } = response.data;

    // Store temporary token
    localStorage.setItem('token', temporaryToken);

    return {
      success: true,
      token: temporaryToken
    };
  } catch (error) {
    console.error('Recovery code error:', error);
    return {
      success: false,
      error: error.response?.data?.error || error.message || 'Invalid recovery code'
    };
  }
}
