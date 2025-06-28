import assert from 'assert';
import { getMonthlyExpenses, getMonthlyIncome, getTagSpendings, getRecentRecords } from '../frontend/data/sampleData.js';

/**
 * Simple tests for data retrieval functions using mocked fetch.
 */
async function run() {
  const expenseData = [
    { amount: 100, description: 'Food', created_at: 1705276800 },
    { amount: 200, description: 'Rent', created_at: 1707523200 }
  ];
  const incomeData = [
    { amount: 300, description: 'salary', created_at: 1704412800 },
    { amount: 200, description: 'bonus', created_at: 1710892800 }
  ];
  global.fetch = async (url) => {
    return {
      async json() {
        if (url === '/expenses') return expenseData;
        if (url === '/incomes') return incomeData;
        throw new Error('unknown url');
      }
    };
  };

  const expenses = await getMonthlyExpenses();
  assert.strictEqual(expenses.length, 12, 'Expenses array should have 12 months');
  assert.strictEqual(expenses[0], 100);
  assert.strictEqual(expenses[1], 200);

  const incomes = await getMonthlyIncome();
  assert.strictEqual(incomes[0], 300);
  assert.strictEqual(incomes[2], 200);

  const tags = await getTagSpendings();
  assert.ok(Array.isArray(tags) && tags.length === 2, 'Tag data should contain two tags');

  const recent = await getRecentRecords();
  assert.ok(Array.isArray(recent.expenses), 'Recent expenses should be an array');
  assert.ok(Array.isArray(recent.incomes), 'Recent incomes should be an array');

  console.log('All tests passed');
}

run();
