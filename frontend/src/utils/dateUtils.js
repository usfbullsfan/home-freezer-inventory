/**
 * Date utility functions for handling timezone-aware date operations
 */

/**
 * Parse a date string as a local date (not UTC)
 * @param {string} dateString - Date string in YYYY-MM-DD format
 * @returns {Date} Date object in local timezone
 */
export function parseLocalDate(dateString) {
  if (!dateString) return null;

  // Parse as local date by splitting components
  // This prevents JavaScript from treating "YYYY-MM-DD" as UTC
  const [year, month, day] = dateString.split('-').map(Number);
  return new Date(year, month - 1, day); // month is 0-indexed
}

/**
 * Format a date string for display in user's local timezone
 * @param {string} dateString - ISO date string from API
 * @returns {string} Formatted date string
 */
export function formatLocalDate(dateString) {
  if (!dateString) return 'N/A';

  const date = parseLocalDate(dateString);
  return date.toLocaleDateString();
}

/**
 * Calculate days between two dates
 * @param {string} startDateString - Start date (YYYY-MM-DD)
 * @param {string} endDateString - End date (YYYY-MM-DD), defaults to today
 * @returns {number} Number of days (can be negative if start is after end)
 */
export function daysBetween(startDateString, endDateString = null) {
  const startDate = parseLocalDate(startDateString);
  const endDate = endDateString ? parseLocalDate(endDateString) : new Date();

  // Reset time to midnight for accurate day comparison
  startDate.setHours(0, 0, 0, 0);
  endDate.setHours(0, 0, 0, 0);

  const diffTime = endDate - startDate;
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

  return diffDays;
}

/**
 * Get date in YYYY-MM-DD format for use in date inputs
 * @param {Date} date - Date object, defaults to today
 * @returns {string} Date string in YYYY-MM-DD format
 */
export function toDateInputValue(date = new Date()) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}
