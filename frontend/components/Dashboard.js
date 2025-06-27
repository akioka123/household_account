import LineChart from './LineChart.js';
import { getMonthlyExpenses, getMonthlyIncome, getTagSpendings } from '../data/sampleData.js';
import NavBar from './NavBar.js';

/**
 * Dashboard screen rendering three line charts and navigation buttons.
 * @module Dashboard
 */
export default function Dashboard() {
  const root = document.createElement('div');
  root.appendChild(NavBar());

  const expenseCanvas = document.createElement('canvas');
  const incomeCanvas = document.createElement('canvas');
  const tagCanvas = document.createElement('canvas');
  root.appendChild(expenseCanvas);
  root.appendChild(incomeCanvas);
  root.appendChild(tagCanvas);

  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

  new LineChart(expenseCanvas, months, getMonthlyExpenses(), '支出', 'rgba(255, 99, 132, 1)');
  new LineChart(incomeCanvas, months, getMonthlyIncome(), '収入', 'rgba(54, 162, 235, 1)');

  const tagData = getTagSpendings();
  tagData.forEach((d, index) => {
    new LineChart(tagCanvas, months, d.amounts, d.tag, `hsl(${index * 60}, 70%, 50%)`);
  });

  return root;
}
