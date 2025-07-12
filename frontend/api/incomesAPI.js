/**
 * API helpers for managing incomes via the backend.
 * @module incomesAPI
 */

/**
 * Retrieve all income records from the backend.
 * @returns {Promise<object[]>} Array of income objects.
 */
export async function fetchIncomes() {
  const res = await fetch('/incomes');
  return res.json();
}

/**
 * Create a new income record.
 *
 * @param {number} amount - Income amount.
 * @param {string} description - Description text.
 * @param {string} targetMonth - Target month in YYYY-MM format.
 * @returns {Promise<Response>} Fetch response.
 */
export async function createIncome(amount, description, targetMonth) {
  return fetch('/incomes', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ amount, description, targetMonth })
  });
}

/**
 * Update an existing income record.
 *
 * @param {number} id - Income identifier.
 * @param {number} amount - New amount value.
 * @param {string} description - Updated description text.
 * @param {string} targetMonth - Target month in YYYY-MM format.
 * @returns {Promise<Response>} Fetch response.
 */
export async function updateIncome(id, amount, description, targetMonth) {
  return fetch(`/incomes/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ amount, description, targetMonth })
  });
}

/**
 * Delete an income record.
 *
 * @param {number} id - Income identifier to remove.
 * @returns {Promise<Response>} Fetch response.
 */
export async function deleteIncome(id) {
  return fetch(`/incomes/${id}`, { method: 'DELETE' });
}
