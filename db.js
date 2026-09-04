import Database from 'better-sqlite3';
import path from 'path';

/**
 * Database utilities for managing expenses and incomes.
 * @module db
 */

const dbPath = process.env.DB_FILE || path.join(process.cwd(), 'data.sqlite');

/**
 * SQLite database instance.
 * @type {import('better-sqlite3').Database}
 */
export const db = new Database(dbPath);

db.exec(`
CREATE TABLE IF NOT EXISTS expenses (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  amount INTEGER NOT NULL,
  description TEXT,
  target_month TEXT NOT NULL DEFAULT (strftime('%Y-%m','now')),
  created_at INTEGER DEFAULT (strftime('%s','now')),
  fixed_item_id INTEGER
);
CREATE TABLE IF NOT EXISTS incomes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  amount INTEGER NOT NULL,
  description TEXT,
  target_month TEXT NOT NULL DEFAULT (strftime('%Y-%m','now')),
  created_at INTEGER DEFAULT (strftime('%s','now'))
);
CREATE TABLE IF NOT EXISTS cash_starts (
  month TEXT PRIMARY KEY,
  amount INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS cash_withdrawals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  month TEXT NOT NULL,
  amount INTEGER NOT NULL,
  created_at INTEGER DEFAULT (strftime('%s','now'))
);
CREATE TABLE IF NOT EXISTS fixed_expense_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  amount INTEGER NOT NULL,
  description TEXT NOT NULL,
  start_month TEXT NOT NULL,
  end_month TEXT,
  is_active INTEGER NOT NULL DEFAULT 1,
  created_at INTEGER DEFAULT (strftime('%s','now'))
);
`);

/**
 * Inserts an expense record.
 * @param {number} amount - Expense amount.
 * @param {string} [description] - Optional description.
 * @returns {number} Inserted row ID.
 */
export function addExpense(amount, description = '', targetMonth = new Date().toISOString().slice(0, 7)) {
  const stmt = db.prepare('INSERT INTO expenses (amount, description, target_month) VALUES (?, ?, ?)');
  const info = stmt.run(amount, description, targetMonth);
  return Number(info.lastInsertRowid);
}

/**
 * Retrieves all expenses.
 * @returns {object[]} List of expense rows.
 */
export function getExpenses() {
  return db.prepare('SELECT * FROM expenses').all();
}

/**
 * Deletes an expense record by ID.
 * @param {number} id - Expense identifier to remove.
 * @returns {void}
 */
export function deleteExpense(id) {
  const stmt = db.prepare('DELETE FROM expenses WHERE id = ?');
  stmt.run(id);
}

/**
 * Updates an existing expense record.
 * @param {number} id - Expense identifier.
 * @param {number} amount - New amount value.
 * @param {string} description - Updated description text.
 * @returns {void}
 */
export function updateExpense(id, amount, description, targetMonth) {
  const stmt = db.prepare('UPDATE expenses SET amount = ?, description = ?, target_month = ? WHERE id = ?');
  stmt.run(amount, description, targetMonth, id);
}

/**
 * Inserts an income record.
 * @param {number} amount - Income amount.
 * @param {string} [description] - Optional description.
 * @returns {number} Inserted row ID.
 */
export function addIncome(amount, description = '', targetMonth = new Date().toISOString().slice(0, 7)) {
  const stmt = db.prepare('INSERT INTO incomes (amount, description, target_month) VALUES (?, ?, ?)');
  const info = stmt.run(amount, description, targetMonth);
  return Number(info.lastInsertRowid);
}

/**
 * Retrieves all incomes.
 * @returns {object[]} List of income rows.
 */
export function getIncomes() {
  return db.prepare('SELECT * FROM incomes').all();
}

/**
 * Deletes an income record by ID.
 * @param {number} id - Income identifier to remove.
 * @returns {void}
 */
export function deleteIncome(id) {
  const stmt = db.prepare('DELETE FROM incomes WHERE id = ?');
  stmt.run(id);
}

/**
 * Retrieves incomes for a specific month and year.
 * @param {number} year - The year.
 * @param {number} month - The month (1-12).
 * @returns {object[]} List of income rows for the specified month.
 */
export function getIncomesByMonth(year, month) {
  const ym = `${year}-${String(month).padStart(2, '0')}`;
  return db.prepare('SELECT * FROM incomes WHERE target_month = ? ORDER BY created_at DESC').all(ym);
}

/**
 * Updates an income record.
 * @param {number} id - The ID of the income record to update.
 * @param {number} amount - The new amount.
 * @param {string} description - The new description.
 * @returns {object} Run result information.
 */
export function updateIncome(id, amount, description, targetMonth) {
  const stmt = db.prepare('UPDATE incomes SET amount = ?, description = ?, target_month = ? WHERE id = ?');
  return stmt.run(amount, description, targetMonth, id);
}

/**
 * Registers a fixed expense item.
 * @param {number} amount - Fixed expense amount.
 * @param {string} description - Fixed expense description.
 * @param {string} startMonth - Application start month (YYYY-MM).
 * @returns {number} Inserted fixed expense item ID.
 */
export function addFixedExpenseItem(amount, description, startMonth) {
  const statement = db.prepare(
    'INSERT INTO fixed_expense_items (amount, description, start_month) VALUES (?, ?, ?)'
  );
  const info = statement.run(amount, description, startMonth);
  return Number(info.lastInsertRowid);
}

/**
 * Ends application of a fixed expense item from the specified month.
 * @param {number} id - Fixed expense item ID.
 * @param {string} endMonth - End month (YYYY-MM).
 * @returns {void}
 */
export function endFixedExpenseItem(id, endMonth) {
  db.prepare('UPDATE fixed_expense_items SET end_month = ?, is_active = 0 WHERE id = ?').run(endMonth, id);
}

/**
 * Applies active fixed expense items to the target month if not yet reflected.
 * @param {string} targetMonth - Target month (YYYY-MM).
 * @returns {number[]} Inserted expense IDs.
 */
export function applyFixedExpensesForMonth(targetMonth) {
  const fixedItems = db.prepare(`
    SELECT id, amount, description
    FROM fixed_expense_items
    WHERE start_month <= ?
      AND (end_month IS NULL OR end_month > ?)
      AND is_active = 1
  `).all(targetMonth, targetMonth);
  const insertedIds = [];
  const findStatement = db.prepare(
    'SELECT id FROM expenses WHERE target_month = ? AND fixed_item_id = ?'
  );
  const insertStatement = db.prepare(
    'INSERT INTO expenses (amount, description, target_month, fixed_item_id) VALUES (?, ?, ?, ?)'
  );
  fixedItems.forEach((fixedItem) => {
    const existing = findStatement.get(targetMonth, fixedItem.id);
    if (!existing) {
      const info = insertStatement.run(
        fixedItem.amount,
        fixedItem.description,
        targetMonth,
        fixedItem.id
      );
      insertedIds.push(Number(info.lastInsertRowid));
    }
  });
  return insertedIds;
}

/**
 * Get previous month string for YYYY-MM format.
 * @param {string} ym - Current year-month string.
 * @returns {string} Previous year-month string.
 */
function previousMonth(ym) {
  const [y, m] = ym.split('-').map(Number);
  const d = new Date(y, m - 1);
  d.setMonth(d.getMonth() - 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
}

/**
 * Insert or replace a monthly starting cash amount.
 * If previous month exists, an expense record named '現金' is added
 * using the formula: previous start + withdrawals - current start.
 *
 * @param {string} month - Year-month string in YYYY-MM format.
 * @param {number} amount - Starting cash amount.
 * @returns {void}
 */
export function insertCashStart(month, amount) {
  const stmt = db.prepare('INSERT OR REPLACE INTO cash_starts (month, amount) VALUES (?, ?)');
  stmt.run(month, amount);
}

/**
 * Retrieve starting cash for a month.
 * @param {string} month - Year-month string.
 * @returns {{month:string, amount:number}|undefined} Start row.
 */
export function selectCashStart(month) {
  return db.prepare('SELECT month, amount FROM cash_starts WHERE month = ?').get(month);
}

/**
 * Insert a cash withdrawal record.
 * @param {string} month - Year-month string.
 * @param {number} amount - Withdrawal amount.
 * @returns {number} Inserted row ID.
 */
export function insertCashWithdrawal(month, amount) {
  const stmt = db.prepare('INSERT INTO cash_withdrawals (month, amount) VALUES (?, ?)');
  const info = stmt.run(month, amount);
  return Number(info.lastInsertRowid);
}

/**
 * Retrieve withdrawals for a month.
 * @param {string} month - Year-month string.
 * @returns {Array<{id:number, month:string, amount:number, created_at:number}>} Rows.
 */
export function selectCashWithdrawals(month) {
  return db.prepare('SELECT * FROM cash_withdrawals WHERE month = ? ORDER BY created_at').all(month);
}
