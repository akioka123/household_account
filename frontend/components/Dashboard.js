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
  root.appendChild(NavBar());

  const expenseCanvas = document.createElement('canvas');
  expenseCanvas.className = 'w-full h-64';
  const incomeCanvas = document.createElement('canvas');
  incomeCanvas.className = 'w-full h-64';
  const tagCanvas = document.createElement('canvas');
  tagCanvas.className = 'w-full h-64';
  const chartContainer = document.createElement('div');
  chartContainer.className = 'w-full max-w-3xl grid grid-cols-1 gap-4';
  chartContainer.appendChild(expenseCanvas);
  chartContainer.appendChild(incomeCanvas);
  chartContainer.appendChild(tagCanvas);
  root.appendChild(chartContainer);

  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

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

