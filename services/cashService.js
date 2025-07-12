/**
 * Service layer for handling cash flow logic.
 * @module services/cashService
 */
import {
  addExpense,
  insertCashStart,
  selectCashStart,
  insertCashWithdrawal,
  selectCashWithdrawals
} from '../db.js';

/**
 * Calculate the previous month string.
 * @param {string} ym - Year-month string in YYYY-MM format.
 * @returns {string} Previous month in YYYY-MM format.
 */
function previousMonth(ym) {
  const [y, m] = ym.split('-').map(Number);
  const d = new Date(y, m - 1);
  d.setMonth(d.getMonth() - 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
}

/**
 * Register a starting cash amount. Also records cash usage as an expense for the
 * previous month if applicable.
 *
 * @param {string} month - Target month.
 * @param {number} amount - Starting cash amount.
 * @returns {void}
 */
export function registerCashStart(month, amount) {
  insertCashStart(month, amount);

  const prev = previousMonth(month);
  const prevRow = selectCashStart(prev);
  if (prevRow) {
    const withdrawals = selectCashWithdrawals(prev);
    const sum = withdrawals.reduce((s, w) => s + w.amount, 0);
    const usage = prevRow.amount + sum - amount;
    if (usage !== 0) {
      addExpense(usage, '現金', prev);
    }
  }
}

/**
 * Retrieve starting cash for a month.
 * @param {string} month - Target month.
 * @returns {{month:string, amount:number}|undefined} Row object.
 */
export function getCashStart(month) {
  return selectCashStart(month);
}

/**
 * Record a cash withdrawal.
 * @param {string} month - Target month.
 * @param {number} amount - Withdrawal amount.
 * @returns {number} Inserted row id.
 */
export function recordWithdrawal(month, amount) {
  return insertCashWithdrawal(month, amount);
}

/**
 * Retrieve withdrawals for a month.
 * @param {string} month - Target month.
 * @returns {Array<{id:number, month:string, amount:number, created_at:number}>}
 *   Array of rows.
 */
export function getWithdrawals(month) {
  return selectCashWithdrawals(month);
}
