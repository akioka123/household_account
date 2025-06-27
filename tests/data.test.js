import assert from 'assert';
import { getMonthlyExpenses, getMonthlyIncome, getTagSpendings } from '../frontend/data/sampleData.js';

/**
 * Simple tests for sample data generation functions.
 */
function run() {
  assert.strictEqual(getMonthlyExpenses().length, 12, 'Expenses should have 12 entries');
  assert.strictEqual(getMonthlyIncome().length, 12, 'Income should have 12 entries');
  const tags = getTagSpendings();
  assert.ok(Array.isArray(tags) && tags.length > 0, 'Tag data should be non-empty');
  console.log('All tests passed');
}

run();
