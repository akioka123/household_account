import LineChart from './LineChart.js';
import { getMonthlyExpenses, getMonthlyIncome, getTagSpendings, getRecentRecords } from '../data/sampleData.js';
import NavBar from './NavBar.js';

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

  const expenseCanvas = document.createElement('canvas');
  expenseCanvas.className = 'w-full h-64';
  const incomeCanvas = document.createElement('canvas');
  incomeCanvas.className = 'w-full h-64';
  const tagCanvas = document.createElement('canvas');
  tagCanvas.className = 'w-full h-64';
  const chartContainer = document.createElement('div');
  chartContainer.className = 'grid grid-cols-1 gap-4';
  chartContainer.appendChild(expenseCanvas);
  chartContainer.appendChild(incomeCanvas);
  chartContainer.appendChild(tagCanvas);

  const wrapper = document.createElement('div');
  wrapper.className = 'w-full max-w-5xl grid grid-cols-1 md:grid-cols-2 gap-4';
  wrapper.appendChild(chartContainer);

  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

  const halfYearContainer = document.createElement('div');
  halfYearContainer.className = 'grid grid-cols-1 gap-4';

  const createHalfTable = (title, start, expenses, income) => {
    const table = document.createElement('table');
    table.className = 'min-w-full text-sm text-left border';
    table.innerHTML = `<caption class="font-bold">${title}</caption><thead><tr><th class="border px-2">月</th><th class="border px-2">支出</th><th class="border px-2">収入</th></tr></thead><tbody></tbody>`;
    for (let i = start; i < start + 6; i++) {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td class="border px-2">${months[i]}</td><td class="border px-2 text-right">${expenses[i]}</td><td class="border px-2 text-right">${income[i]}</td>`;
      table.querySelector('tbody').appendChild(tr);
    }
    return table;
  };

  const [expenses, income, tagData] = await Promise.all([
    getMonthlyExpenses(),
    getMonthlyIncome(),
    getTagSpendings()
  ]);

  new LineChart(expenseCanvas, months, expenses, '支出', 'rgba(255, 99, 132, 1)');
  new LineChart(incomeCanvas, months, income, '収入', 'rgba(54, 162, 235, 1)');

  tagData.forEach((d, index) => {
    new LineChart(tagCanvas, months, d.amounts, d.tag, `hsl(${index * 60}, 70%, 50%)`);
  });

  halfYearContainer.appendChild(createHalfTable('前半6ヶ月', 0, expenses, income));
  halfYearContainer.appendChild(createHalfTable('後半6ヶ月', 6, expenses, income));
  wrapper.appendChild(halfYearContainer);
  root.appendChild(wrapper);

  const recent = await getRecentRecords();
  const listContainer = document.createElement('div');
  listContainer.className = 'w-full max-w-3xl grid grid-cols-1 md:grid-cols-2 gap-4 mt-6';

  const expTable = document.createElement('table');
  expTable.className = 'min-w-full text-sm text-left border';
  expTable.innerHTML = '<caption class="font-bold">最近6ヶ月の支出</caption><thead><tr><th class="border px-2">日付</th><th class="border px-2">内容</th><th class="border px-2">金額</th></tr></thead><tbody></tbody>';
  recent.expenses.forEach((e) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td class="border px-2">${new Date(e.created_at * 1000).toLocaleDateString()}</td><td class="border px-2">${e.description || ''}</td><td class="border px-2 text-right">${e.amount}</td>`;
    expTable.querySelector('tbody').appendChild(tr);
  });

  const incTable = document.createElement('table');
  incTable.className = 'min-w-full text-sm text-left border';
  incTable.innerHTML = '<caption class="font-bold">最近6ヶ月の収入</caption><thead><tr><th class="border px-2">日付</th><th class="border px-2">内容</th><th class="border px-2">金額</th></tr></thead><tbody></tbody>';
  recent.incomes.forEach((i) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td class="border px-2">${new Date(i.created_at * 1000).toLocaleDateString()}</td><td class="border px-2">${i.description || ''}</td><td class="border px-2 text-right">${i.amount}</td>`;
    incTable.querySelector('tbody').appendChild(tr);
  });

  listContainer.appendChild(expTable);
  listContainer.appendChild(incTable);
  root.appendChild(listContainer);

  return root;
}

