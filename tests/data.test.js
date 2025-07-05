import assert from 'assert';
import { getMonthlyExpenses, getMonthlyIncome, getTagSpendings, getRecentRecords } from '../frontend/data/sampleData.js';

/**
 * Simple tests for data retrieval functions using mocked fetch.
 */
async function run() {
  const expenseData = [
    { amount: 100, description: 'Food', created_at: 1705276800, target_month: '2024-01' },
    { amount: 200, description: 'Rent', created_at: 1707523200, target_month: '2024-02' }
  ];
  const incomeData = [
    { amount: 300, description: 'salary', created_at: 1704412800, target_month: '2024-01' },
    { amount: 200, description: 'bonus', created_at: 1710892800, target_month: '2024-03' }
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

  const year = new Date(expenseData[0].created_at * 1000).getFullYear();

  const expenses = await getMonthlyExpenses(year);
  assert.strictEqual(expenses.length, 12, 'Expenses array should have 12 months');
  assert.strictEqual(expenses[0], 100);
  assert.strictEqual(expenses[1], 200);

  const emptyExpenses = await getMonthlyExpenses(year - 1);
  assert.ok(emptyExpenses.every(v => v === 0), 'Different year returns zeros');

  const incomes = await getMonthlyIncome(year);
  assert.strictEqual(incomes[0], 300);
  assert.strictEqual(incomes[2], 200);

  const emptyIncomes = await getMonthlyIncome(year - 1);
  assert.ok(emptyIncomes.every(v => v === 0), 'Different year incomes are zero');

  const tags = await getTagSpendings(year);
  assert.ok(Array.isArray(tags) && tags.length === 2, 'Tag data should contain two tags');

  const recent = await getRecentRecords();
  assert.ok(Array.isArray(recent.expenses), 'Recent expenses should be an array');
  assert.ok(Array.isArray(recent.incomes), 'Recent incomes should be an array');

  console.log('All tests passed');
}

run();
