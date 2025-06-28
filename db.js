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
  created_at INTEGER DEFAULT (strftime('%s','now'))
);
CREATE TABLE IF NOT EXISTS incomes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  amount INTEGER NOT NULL,
  description TEXT,
  created_at INTEGER DEFAULT (strftime('%s','now'))
);
`);

/**
 * Inserts an expense record.
 * @param {number} amount - Expense amount.
 * @param {string} [description] - Optional description.
 * @returns {number} Inserted row ID.
 */
export function addExpense(amount, description = '') {
  const stmt = db.prepare('INSERT INTO expenses (amount, description) VALUES (?, ?)');
  const info = stmt.run(amount, description);
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
 * Updates an existing expense record.
 * @param {number} id - Expense identifier.
 * @param {number} amount - New amount value.
 * @param {string} description - Updated description text.
 * @returns {void}
 */
export function updateExpense(id, amount, description) {
  const stmt = db.prepare('UPDATE expenses SET amount = ?, description = ? WHERE id = ?');
  stmt.run(amount, description, id);
}

/**
 * Inserts an income record.
 * @param {number} amount - Income amount.
 * @param {string} [description] - Optional description.
 * @returns {number} Inserted row ID.
 */
export function addIncome(amount, description = '') {
  const stmt = db.prepare('INSERT INTO incomes (amount, description) VALUES (?, ?)');
  const info = stmt.run(amount, description);
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
 * Retrieves incomes for a specific month and year.
 * @param {number} year - The year.
 * @param {number} month - The month (1-12).
 * @returns {object[]} List of income rows for the specified month.
 */
export function getIncomesByMonth(year, month) {
  const startOfMonth = new Date(year, month - 1, 1).getTime() / 1000;
  const endOfMonth = new Date(year, month, 0).getTime() / 1000;
  return db.prepare('SELECT * FROM incomes WHERE created_at >= ? AND created_at <= ? ORDER BY created_at DESC').all(startOfMonth, endOfMonth);
}

/**
 * Updates an income record.
 * @param {number} id - The ID of the income record to update.
 * @param {number} amount - The new amount.
 * @param {string} description - The new description.
 * @returns {object} Run result information.
 */
export function updateIncome(id, amount, description) {
  const stmt = db.prepare('UPDATE incomes SET amount = ?, description = ? WHERE id = ?');
  return stmt.run(amount, description, id);
}
