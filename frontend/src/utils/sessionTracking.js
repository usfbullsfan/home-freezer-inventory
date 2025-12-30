/**
 * Session tracking utilities for managing recently added items
 */

const SESSION_KEY = 'freezer_add_session';
const SESSION_DURATION = 24 * 60 * 60 * 1000; // 24 hours in milliseconds

/**
 * Get current session data
 * @returns {Object} Session object with itemIds array and timestamp
 */
export function getSession() {
  try {
    const sessionData = localStorage.getItem(SESSION_KEY);
    if (!sessionData) return null;

    const session = JSON.parse(sessionData);

    // Check if session has expired
    if (Date.now() - session.timestamp > SESSION_DURATION) {
      clearSession();
      return null;
    }

    return session;
  } catch (error) {
    console.error('Error reading session:', error);
    return null;
  }
}

/**
 * Add an item ID to the current session
 * @param {number} itemId - ID of the newly added item
 */
export function addItemToSession(itemId) {
  try {
    const session = getSession() || { itemIds: [], timestamp: Date.now() };

    // Add item if not already in session
    if (!session.itemIds.includes(itemId)) {
      session.itemIds.push(itemId);
      session.timestamp = Date.now(); // Update timestamp
      localStorage.setItem(SESSION_KEY, JSON.stringify(session));
    }
  } catch (error) {
    console.error('Error adding item to session:', error);
  }
}

/**
 * Clear the current session
 */
export function clearSession() {
  try {
    localStorage.removeItem(SESSION_KEY);
  } catch (error) {
    console.error('Error clearing session:', error);
  }
}

/**
 * Get count of items in current session
 * @returns {number} Number of items in session
 */
export function getSessionItemCount() {
  const session = getSession();
  return session ? session.itemIds.length : 0;
}

/**
 * Get all item IDs from current session
 * @returns {number[]} Array of item IDs
 */
export function getSessionItemIds() {
  const session = getSession();
  return session ? session.itemIds : [];
}
