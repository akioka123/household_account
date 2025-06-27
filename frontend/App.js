import Dashboard from './components/Dashboard.js';

/**
 * Application entry point. Renders the Dashboard component.
 * @module App
 */
function main() {
  const root = document.getElementById('root');
  root.replaceChildren(Dashboard());
}

window.addEventListener('DOMContentLoaded', main);
