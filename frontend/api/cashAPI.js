/**
 * API helpers for cash management endpoints.
 * @module cashAPI
 */

/**
 * Fetch starting cash for a month.
 * @param {number|string} year - Year component.
 * @param {number|string} month - Month component.
 * @returns {Promise<{month:string, amount:number}|{}>} Response JSON.
 */
export async function fetchCashStart(year, month) {
  const res = await fetch(`/cash/start/${year}/${month}`);
  return res.json();
}

/**
 * Register starting cash.
 * @param {string} month - Month string in YYYY-MM format.
 * @param {number} amount - Amount value.
 * @returns {Promise<Response>} Fetch response.
 */
export async function registerCashStartAPI(month, amount) {
  return fetch('/cash/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ month, amount })
  });
}

/**
 * Fetch withdrawals for a month.
 * @param {number|string} year - Year component.
 * @param {number|string} month - Month component.
 * @returns {Promise<object[]>} Array of withdrawal rows.
 */
export async function fetchWithdrawals(year, month) {
  const res = await fetch(`/cash/withdraw/${year}/${month}`);
  return res.json();
}

/**
 * Register a new withdrawal.
 * @param {string} month - Month string in YYYY-MM format.
 * @param {number} amount - Withdrawal amount.
 * @returns {Promise<Response>} Fetch response.
 */
export async function createWithdrawal(month, amount) {
  return fetch('/cash/withdraw', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ month, amount })
  });
}
