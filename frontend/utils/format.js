/**
 * Utilities for formatting numbers for display.
 * @module format
 */

/**
 * Format an amount with comma as thousand separator.
 * @param {number} amount - Numeric amount to format.
 * @returns {string} Formatted string with comma separators.
 */
export function formatAmount(amount) {
  return Number(amount).toLocaleString('ja-JP');
}
