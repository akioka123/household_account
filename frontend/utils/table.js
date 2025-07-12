import { formatAmount } from "./format.js";

/**
 * Utility functions for creating table elements.
 * @module table
 */

/**
 * Create a summary table for a 12 month range ending at the given year-month.
 *
 * @param {number} year - End year.
 * @param {number} month - End month (1-12).
 * @param {Object<number, number[]>} expensesMap - Expense totals by year.
 * @param {Object<number, number[]>} incomeMap - Income totals by year.
 * @returns {HTMLTableElement} Rendered table element.
 */
export function createRangeTable(year, month, expensesMap, incomeMap) {
  const start = new Date(year, month - 12);
  const caption = `${start.getFullYear()}/${String(start.getMonth() + 1).padStart(2, '0')}〜${year}/${String(month).padStart(2, '0')}`;
  const table = document.createElement('table');
  table.className = 'min-w-full text-sm text-left border';
  table.innerHTML = `<caption class="font-bold">${caption}</caption><thead><tr><th class="border px-2">年月</th><th class="border px-2">収入</th><th class="border px-2">支出</th><th class="border px-2">損益</th></tr></thead><tbody></tbody>`;
  for (let i = 0; i < 12; i++) {
    const d = new Date(year, month - 1 - i);
    const y = d.getFullYear();
    const m = d.getMonth();
    const exp = (expensesMap[y] || [])[m] || 0;
    const inc = (incomeMap[y] || [])[m] || 0;
    const diff = inc - exp;
    const diffClass = diff < 0 ? ' text-red-600' : '';
    const ym = `${y}/${String(m + 1).padStart(2, '0')}`;
    const tr = document.createElement('tr');
    tr.innerHTML = `<td class="border px-2">${ym}</td><td class="border px-2 text-right">${formatAmount(inc)}</td><td class="border px-2 text-right">${formatAmount(exp)}</td><td class="border px-2 text-right${diffClass}">${formatAmount(diff)}</td>`;
    table.querySelector('tbody').appendChild(tr);
  }
  return table;
}
