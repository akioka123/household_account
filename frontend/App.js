import Dashboard from './components/Dashboard.js';
import ExpenseForm from './components/ExpenseForm.js';
import IncomeForm from './components/IncomeForm.js';
import ExpensesList from './components/ExpensesList.js';

/**
 * Application entry point. Renders components based on location hash.
 * @module App
 */

/**
 * Renders the page based on the current location hash.
 * @returns {Promise<void>}
 */
async function render() {
  const root = document.getElementById('root');
  const hash = window.location.hash;
  if (hash === '#expense') {
    root.replaceChildren(ExpenseForm());
  } else if (hash === '#expenses') {
    root.replaceChildren(await ExpensesList());
  } else if (hash === '#income') {
    root.replaceChildren(IncomeForm());
  } else {
    root.replaceChildren(await Dashboard());
  }
}

window.addEventListener('DOMContentLoaded', () => { render(); });
window.addEventListener('hashchange', () => { render(); });

