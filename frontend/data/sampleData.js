/**
 * @module sampleData
 * Provides data retrieval functions for charts.
 */

/**
 * Aggregates amounts by calendar month.
 * @param {Array<{amount:number,created_at:number}>} items - Records to aggregate
 * @returns {number[]} Amount totals per month index (0-11)
 */
function groupByMonth(items) {
  const result = Array(12).fill(0);
  items.forEach((it) => {
    const date = new Date(it.created_at * 1000);
    const month = date.getMonth();
    result[month] += it.amount;
  });
  return result;
}

/**
 * Fetch monthly expense amounts from the backend.
 * @returns {Promise<number[]>} Monthly expense totals
 */
export async function getMonthlyExpenses() {
  const res = await fetch('/expenses');
  const data = await res.json();
  return groupByMonth(data);
}

/**
 * Fetch monthly income amounts from the backend.
 * @returns {Promise<number[]>} Monthly income totals
 */
export async function getMonthlyIncome() {
  const res = await fetch('/incomes');
  const data = await res.json();
  return groupByMonth(data);
}

/**
 * Fetch expenses and calculate tag-based spending amounts.
 * @returns {Promise<Object<string, number[]>[]>} Tag-based monthly expense data
 */
export async function getTagSpendings() {
  const res = await fetch('/expenses');
  const data = await res.json();
  const tagMap = {};
  data.forEach((it) => {
    const tag = it.description || 'その他';
    if (!tagMap[tag]) {
      tagMap[tag] = Array(12).fill(0);
    }
    const date = new Date(it.created_at * 1000);
    const month = date.getMonth();
    tagMap[tag][month] += it.amount;
  });
  return Object.entries(tagMap).map(([tag, amounts]) => ({ tag, amounts }));
}
