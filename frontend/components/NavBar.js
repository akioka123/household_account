/**
 * Navigation bar component with links to registration pages.
 * @module NavBar
 */

export default function NavBar() {
  const container = document.createElement('div');
  container.className = 'nav-bar';

  const homeLink = document.createElement('a');
  homeLink.href = '#';
  homeLink.textContent = 'ダッシュボード';
  container.appendChild(homeLink);

  const expenseLink = document.createElement('a');
  expenseLink.href = '#expense';
  expenseLink.textContent = '支出登録';
  container.appendChild(expenseLink);

  const incomeLink = document.createElement('a');
  incomeLink.href = '#income';
  incomeLink.textContent = '収入登録';
  container.appendChild(incomeLink);

  return container;
}
