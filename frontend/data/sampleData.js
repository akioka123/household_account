/**
 * @module sampleData
 * Provides sample datasets for line charts in the dashboard.
 */

/**
 * Returns monthly expense amounts for 12 months.
 * @returns {number[]} Monthly expense data
 */
export function getMonthlyExpenses() {
  return [50000, 48000, 52000, 51000, 53000, 55000, 54000, 56000, 58000, 60000, 59000, 61000];
}

/**
 * Returns monthly income amounts for 12 months.
 * @returns {number[]} Monthly income data
 */
export function getMonthlyIncome() {
  return [300000, 300000, 300000, 300000, 320000, 300000, 300000, 300000, 300000, 330000, 300000, 300000];
}

/**
 * Returns tag-based spending amounts for 12 months.
 * @returns {Object<string, number[]>[]} Tag-based monthly expense data
 */
export function getTagSpendings() {
  return [
    { tag: 'Food', amounts: [15000, 14000, 16000, 15500, 16500, 17000, 16800, 17200, 17500, 18000, 17800, 18500] },
    { tag: 'Rent', amounts: [20000, 20000, 20000, 20000, 20000, 20000, 20000, 20000, 20000, 20000, 20000, 20000] },
    { tag: 'Entertainment', amounts: [5000, 6000, 4000, 4500, 5500, 5000, 6500, 6000, 5500, 7000, 6500, 6000] }
  ];
}
