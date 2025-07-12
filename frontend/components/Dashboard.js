import { getMonthlyExpenses, getMonthlyIncome, getTagSpendings, getRecentRecords } from '../data/sampleData.js';
import NavBar from './NavBar.js';
import { formatAmount } from '../utils/format.js';
import { createRangeTable } from '../utils/table.js';
import { createIncomeChart, createExpenseChart, createTagChart } from '../utils/chartSetup.js';

/**
 * Dashboard screen rendering three line charts and navigation buttons.
 * Data is fetched from the backend at runtime.
 * @module Dashboard
 */
/**
 * Renders the dashboard using data from the backend.
 * @returns {Promise<HTMLDivElement>} Root element containing charts
 */
export default async function Dashboard() {
  const root = document.createElement('div');
  root.className = 'min-h-screen flex flex-col items-center p-4 bg-gray-50';
  root.appendChild(NavBar('ダッシュボード'));

  // Create selector to unify y-axis scale across charts.
  // The default is set to 500000 to align with typical monthly totals.
  const scaleSelect = document.createElement('select');
  [100000, 500000, 1000000].forEach((v) => {
    const option = document.createElement('option');
    option.value = v;
    option.textContent = v.toLocaleString();
    scaleSelect.appendChild(option);
  });
  scaleSelect.className = 'border p-1 mb-2 self-end';

  scaleSelect.value = '500000';

  const incomeCanvas = document.createElement('canvas');
  incomeCanvas.className = 'w-full h-64';
  const expenseCanvas = document.createElement('canvas');
  expenseCanvas.className = 'w-full h-64';
  const tagCanvas = document.createElement('canvas');
  tagCanvas.className = 'w-full h-64';

  // Dropdown to switch displayed tag in the bottom chart
  const tagSelect = document.createElement('select');
  tagSelect.className = 'border p-1 mb-2 self-end';

  const chartContainer = document.createElement('div');
  chartContainer.className = 'grid grid-cols-1 gap-4';
  chartContainer.appendChild(scaleSelect);
  chartContainer.appendChild(incomeCanvas);
  chartContainer.appendChild(expenseCanvas);
  chartContainer.appendChild(tagSelect);
  chartContainer.appendChild(tagCanvas);

  const wrapper = document.createElement('div');
  wrapper.className = 'w-full max-w-5xl grid grid-cols-1 md:grid-cols-2 gap-4';
  wrapper.appendChild(chartContainer);

  const months = [
    '1月','2月','3月','4月','5月','6月',
    '7月','8月','9月','10月','11月','12月'
  ];

  const monthInput = document.createElement('input');
  monthInput.type = 'month';
  monthInput.className = 'border p-1 mb-2 self-end';
  const now = new Date();
  monthInput.value = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;

  const yearlyContainer = document.createElement('div');
  yearlyContainer.className = 'grid grid-cols-1 gap-4';


  const [expenses, income, tagData] = await Promise.all([
    getMonthlyExpenses(),
    getMonthlyIncome(),
    getTagSpendings()
  ]);

  const incomeChart = createIncomeChart(
    incomeCanvas,
    months,
    income,
    Number(scaleSelect.value)
  );
  const expenseChart = createExpenseChart(
    expenseCanvas,
    months,
    expenses,
    Number(scaleSelect.value)
  );

  tagData.forEach((d, idx) => {
    const option = document.createElement('option');
    option.value = idx;
    option.textContent = d.tag;
    tagSelect.appendChild(option);
  });

  const tagChart = createTagChart(
    tagCanvas,
    months,
    tagData[0]?.amounts || [],
    tagData[0]?.tag || '',
    Number(scaleSelect.value)
  );

  const currentYear = now.getFullYear();
  const currentMonth = now.getMonth() + 1;
  const [prevExp, prevInc] = await Promise.all([
    getMonthlyExpenses(currentYear - 1),
    getMonthlyIncome(currentYear - 1)
  ]);
  const expenseMap = { [currentYear]: expenses, [currentYear - 1]: prevExp };
  const incomeMap = { [currentYear]: income, [currentYear - 1]: prevInc };
  yearlyContainer.appendChild(createRangeTable(currentYear, currentMonth, expenseMap, incomeMap));
  const summarySection = document.createElement('div');
  summarySection.className = 'flex flex-col';
  summarySection.appendChild(monthInput);
  summarySection.appendChild(yearlyContainer);
  wrapper.appendChild(summarySection);
  root.appendChild(wrapper);

  const recent = await getRecentRecords();
  const listContainer = document.createElement('div');
  listContainer.className = 'w-full max-w-3xl grid grid-cols-1 md:grid-cols-2 gap-4 mt-6';

  const expTable = document.createElement('table');
  expTable.className = 'min-w-full text-sm text-left border';
  expTable.innerHTML = '<caption class="font-bold">最近6ヶ月の支出</caption><thead><tr><th class="border px-2">日付</th><th class="border px-2">内容</th><th class="border px-2">金額</th></tr></thead><tbody></tbody>';
  recent.expenses.forEach((e) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td class="border px-2">${new Date(e.created_at * 1000).toLocaleDateString()}</td><td class="border px-2">${e.description || ''}</td><td class="border px-2 text-right">${formatAmount(e.amount)}</td>`;
    expTable.querySelector('tbody').appendChild(tr);
  });

  const incTable = document.createElement('table');
  incTable.className = 'min-w-full text-sm text-left border';
  incTable.innerHTML = '<caption class="font-bold">最近6ヶ月の収入</caption><thead><tr><th class="border px-2">日付</th><th class="border px-2">内容</th><th class="border px-2">金額</th></tr></thead><tbody></tbody>';
  recent.incomes.forEach((i) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td class="border px-2">${new Date(i.created_at * 1000).toLocaleDateString()}</td><td class="border px-2">${i.description || ''}</td><td class="border px-2 text-right">${formatAmount(i.amount)}</td>`;
    incTable.querySelector('tbody').appendChild(tr);
  });

  listContainer.appendChild(expTable);
  listContainer.appendChild(incTable);
  root.appendChild(listContainer);

  // update all charts when scale is changed
  scaleSelect.addEventListener('change', () => {
    const max = Number(scaleSelect.value);
    expenseChart.setMax(max);
    incomeChart.setMax(max);
    tagChart.setMax(max);
  });

  // switch tag data in bottom chart
  tagSelect.addEventListener('change', () => {
    const idx = Number(tagSelect.value);
    const d = tagData[idx];
    tagChart.updateData(months, d.amounts, d.tag);
  });

  // reload summary when month is changed
  monthInput.addEventListener('change', async () => {
    const year = Number(monthInput.value.split('-')[0]);
    const [exp, expPrev, inc, incPrev] = await Promise.all([
      getMonthlyExpenses(year),
      getMonthlyExpenses(year - 1),
      getMonthlyIncome(year),
      getMonthlyIncome(year - 1)
    ]);
    const expenseData = { [year]: exp, [year - 1]: expPrev };
    const incomeData = { [year]: inc, [year - 1]: incPrev };
    const m = Number(monthInput.value.split('-')[1]);
    yearlyContainer.innerHTML = '';
    yearlyContainer.appendChild(createRangeTable(year, m, expenseData, incomeData));
  });

  return root;
}

