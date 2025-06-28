/**
 * Navigation bar component with links to registration pages.
 * @module NavBar
 */

export default function NavBar() {
  const container = document.createElement('div');
  container.className = 'flex space-x-4 mb-4';

  const homeLink = document.createElement('a');
  homeLink.href = '#';
  homeLink.textContent = 'ダッシュボード';
  homeLink.className = 'text-blue-600 underline';
  container.appendChild(homeLink);

  const expenseLink = document.createElement('a');
  expenseLink.href = '#expense';
  expenseLink.textContent = '支出登録';
  expenseLink.className = 'text-blue-600 underline';
  container.appendChild(expenseLink);


  const incomeLink = document.createElement('a');
  incomeLink.href = '#income';
  incomeLink.textContent = '収入登録';
  incomeLink.className = 'text-blue-600 underline';
  container.appendChild(incomeLink);

  return container;
}
