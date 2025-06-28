import Dashboard from './components/Dashboard.js';
import ExpenseForm from './components/ExpenseForm.js';

/**
 * Application entry point. Renders components based on location hash.
 * @module App
 */
function render() {
  const root = document.getElementById('root');
  const hash = window.location.hash;
  if (hash === '#expense') {
    root.replaceChildren(ExpenseForm());
  } else {
    root.replaceChildren(Dashboard());
  }
}

window.addEventListener('DOMContentLoaded', render);
window.addEventListener('hashchange', render);
