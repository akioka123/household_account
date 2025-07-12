/**
 * API helpers for managing expenses via the backend.
 * @module expensesAPI
 */

/**
 * Retrieve all expense records from the backend.
 * @returns {Promise<object[]>} Array of expense objects.
 */
export async function fetchExpenses() {
  const res = await fetch('/expenses');
  return res.json();
}

/**
 * Create a new expense record.
 *
 * @param {number} amount - Expense amount.
 * @param {string} description - Description text.
 * @param {string} targetMonth - Target month in YYYY-MM format.
 * @returns {Promise<Response>} Fetch response.
 */
export async function createExpense(amount, description, targetMonth) {
  return fetch('/expenses', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ amount, description, targetMonth })
  });
}

/**
 * Update an existing expense record.
 *
 * @param {number} id - Expense identifier.
 * @param {number} amount - New amount value.
 * @param {string} description - Updated description text.
 * @param {string} targetMonth - Target month in YYYY-MM format.
 * @returns {Promise<Response>} Fetch response.
 */
export async function updateExpense(id, amount, description, targetMonth) {
  return fetch(`/expenses/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ amount, description, targetMonth })
  });
}

/**
 * Delete an expense record.
 *
 * @param {number} id - Expense identifier to remove.
 * @returns {Promise<Response>} Fetch response.
 */
export async function deleteExpense(id) {
  return fetch(`/expenses/${id}`, { method: 'DELETE' });
}
