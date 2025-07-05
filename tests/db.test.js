import assert from 'assert';
import fs from 'fs';
import os from 'os';
import path from 'path';

const tmpFile = path.join(os.tmpdir(), `dbtest-${Date.now()}.sqlite`);
process.env.DB_FILE = tmpFile;

const dbModule = await import('../db.js');

dbModule.addExpense(1000, 'coffee', '2024-01');
const expenses = dbModule.getExpenses();
assert.strictEqual(expenses.length, 1, 'One expense should be stored');

dbModule.updateExpense(expenses[0].id, 1500, 'tea', '2024-02');
const updated = dbModule.getExpenses()[0];
assert.strictEqual(updated.amount, 1500, 'Expense amount should be updated');

dbModule.deleteExpense(updated.id);
assert.strictEqual(dbModule.getExpenses().length, 0, 'Expense should be deleted');

dbModule.addIncome(2000, 'salary', '2024-01');
const incomes = dbModule.getIncomes();
assert.strictEqual(incomes.length, 1, 'One income should be stored');

dbModule.updateIncome(incomes[0].id, 2500, 'salary', '2024-02');
const incUpdated = dbModule.getIncomes()[0];
assert.strictEqual(incUpdated.amount, 2500, 'Income amount should be updated');

dbModule.deleteIncome(incUpdated.id);
assert.strictEqual(dbModule.getIncomes().length, 0, 'Income should be deleted');

fs.unlinkSync(tmpFile);
console.log('SQLite tests passed');
