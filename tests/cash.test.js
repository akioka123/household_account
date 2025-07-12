import assert from 'assert';
import fs from 'fs';
import os from 'os';
import path from 'path';

const tmpFile = path.join(os.tmpdir(), `cash-${Date.now()}.sqlite`);
process.env.DB_FILE = tmpFile;

const dbModule = await import('../db.js');
const cashService = await import('../services/cashService.js');

// month start and withdrawal
cashService.registerCashStart('2024-05', 100000);
assert.strictEqual(cashService.getCashStart('2024-05').amount, 100000);

cashService.recordWithdrawal('2024-05', 20000);
assert.strictEqual(cashService.getWithdrawals('2024-05').length, 1);

cashService.registerCashStart('2024-06', 80000);
const cashExpense = dbModule.getExpenses().find(e => e.description === '現金' && e.target_month === '2024-05');
assert.ok(cashExpense, 'cash expense should be added');
assert.strictEqual(cashExpense.amount, 40000);

fs.unlinkSync(tmpFile);
console.log('Cash tests passed');

