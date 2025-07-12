/**
 * Navigation bar component displaying the current screen title and links.
 * @module NavBar
 */

/**
 * Creates a styled navigation bar.
 *
 * @param {string} title - Title of the current screen.
 * @returns {HTMLElement} Navigation element.
 */
export default function NavBar(title) {
  const nav = document.createElement('nav');
  nav.className = 'bg-white shadow flex items-center justify-between p-4 mb-4 w-full';

  const heading = document.createElement('div');
  heading.textContent = title;
  heading.className = 'font-bold text-lg';
  nav.appendChild(heading);

  const linkContainer = document.createElement('div');
  linkContainer.className = 'space-x-4';

  const homeLink = document.createElement('a');
  homeLink.href = '#';
  homeLink.textContent = 'ダッシュボード';
  homeLink.className = 'text-blue-600 hover:underline';
  linkContainer.appendChild(homeLink);

  const expenseLink = document.createElement('a');
  expenseLink.href = '#expense';
  expenseLink.textContent = '支出登録';
  expenseLink.className = 'text-blue-600 hover:underline';
  linkContainer.appendChild(expenseLink);

  const incomeLink = document.createElement('a');
  incomeLink.href = '#income';
  incomeLink.textContent = '収入登録';
  incomeLink.className = 'text-blue-600 hover:underline';
  linkContainer.appendChild(incomeLink);

  const cashLink = document.createElement('a');
  cashLink.href = '#cash';
  cashLink.textContent = '現金管理';
  cashLink.className = 'text-blue-600 hover:underline';
  linkContainer.appendChild(cashLink);

  nav.appendChild(linkContainer);
  return nav;
}

