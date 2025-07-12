import LineChart from '../components/LineChart.js';

/**
 * Factory functions for initializing common charts.
 * @module chartSetup
 */

/**
 * Create a line chart representing income values.
 *
 * @param {HTMLCanvasElement} canvas - Target canvas element.
 * @param {string[]} labels - Labels for the x-axis.
 * @param {number[]} data - Income amounts.
 * @param {number} max - Maximum y-axis value.
 * @returns {LineChart} Initialized chart instance.
 */
export function createIncomeChart(canvas, labels, data, max) {
  return new LineChart(canvas, labels, data, '収入', 'rgba(54, 162, 235, 1)', max);
}

/**
 * Create a line chart representing expense values.
 *
 * @param {HTMLCanvasElement} canvas - Target canvas element.
 * @param {string[]} labels - Labels for the x-axis.
 * @param {number[]} data - Expense amounts.
 * @param {number} max - Maximum y-axis value.
 * @returns {LineChart} Initialized chart instance.
 */
export function createExpenseChart(canvas, labels, data, max) {
  return new LineChart(canvas, labels, data, '支出', 'rgba(255, 99, 132, 1)', max);
}

/**
 * Create a line chart representing tag-based expenses.
 *
 * @param {HTMLCanvasElement} canvas - Target canvas element.
 * @param {string[]} labels - Labels for the x-axis.
 * @param {number[]} data - Expense amounts for the tag.
 * @param {string} tag - Tag label.
 * @param {number} max - Maximum y-axis value.
 * @returns {LineChart} Initialized chart instance.
 */
export function createTagChart(canvas, labels, data, tag, max) {
  return new LineChart(canvas, labels, data, tag, 'rgba(75, 192, 192, 1)', max);
}
