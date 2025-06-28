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
