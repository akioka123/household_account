import assert from 'assert';
import fs from 'fs';
import os from 'os';
import path from 'path';

const tmpFile = path.join(os.tmpdir(), `dbtest-${Date.now()}.sqlite`);
process.env.DB_FILE = tmpFile;

const dbModule = await import('../db.js');

dbModule.addExpense(1000, 'coffee');
const expenses = dbModule.getExpenses();
assert.strictEqual(expenses.length, 1, 'One expense should be stored');

dbModule.updateExpense(expenses[0].id, 1500, 'tea');
const updated = dbModule.getExpenses()[0];
assert.strictEqual(updated.amount, 1500, 'Expense amount should be updated');

dbModule.addIncome(2000, 'salary');
const incomes = dbModule.getIncomes();
assert.strictEqual(incomes.length, 1, 'One income should be stored');

fs.unlinkSync(tmpFile);
console.log('SQLite tests passed');
