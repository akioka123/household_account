import LineChart from './LineChart.js';
import { getMonthlyExpenses, getMonthlyIncome, getTagSpendings } from '../data/sampleData.js';
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
  root.appendChild(NavBar());

  const expenseCanvas = document.createElement('canvas');
  const incomeCanvas = document.createElement('canvas');
  const tagCanvas = document.createElement('canvas');
  root.appendChild(expenseCanvas);
  root.appendChild(incomeCanvas);
  root.appendChild(tagCanvas);

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

  return root;
}

