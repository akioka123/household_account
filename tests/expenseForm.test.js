import assert from 'assert';
import { JSDOM } from 'jsdom';
import ExpenseForm from '../frontend/components/ExpenseForm.js';

/**
 * Integration tests for the unified ExpenseForm component.
 */
async function run() {
  const records = [
    { id: 1, amount: 100, description: 'A', created_at: Date.parse('2024-05-01') / 1000 },
    { id: 2, amount: 200, description: 'B', created_at: Date.parse('2024-05-10') / 1000 },
    { id: 3, amount: 300, description: 'C', created_at: Date.parse('2024-06-01') / 1000 }
  ];
  let postCalled = false;
  let putCalled = false;
  global.fetch = async (url, opts) => {
    if (url === '/expenses' && (!opts || opts.method === 'GET')) {
      return { json: async () => records };
    }
    if (url === '/expenses' && opts && opts.method === 'POST') { postCalled = true; return { ok: true }; }
    if (url.startsWith('/expenses/') && opts && opts.method === 'PUT') { putCalled = true; return { ok: true }; }
    throw new Error('unknown url');
  };

  const dom = new JSDOM('<!DOCTYPE html><body></body>', { url: 'http://localhost' });
  global.document = dom.window.document;
  global.window = dom.window;

  const el = ExpenseForm();
  dom.window.document.body.appendChild(el);
  await new Promise(res => setImmediate(res));

  const monthInput = el.querySelector('input[type="month"]');
  monthInput.value = '2024-05';
  monthInput.dispatchEvent(new dom.window.Event('change'));
  await el.renderPromise;
  const items = el.querySelectorAll('ul li');
  console.log('items len', items.length);
  assert.strictEqual(items.length, 2, 'Should show two records for selected month');

  const form = el.querySelector('form');
  const [amountInput, descInput] = form.querySelectorAll('input');
  amountInput.value = 500;
  descInput.value = 'test';
  form.dispatchEvent(new dom.window.Event('submit'));
  await new Promise(res => setImmediate(res));
  assert.ok(postCalled, 'POST should be called when submitting new expense');

  // trigger edit mode using the DOM API for better JSDOM compatibility
  items[0].querySelector('.edit-btn').click();
  await new Promise(res => setImmediate(res));
  console.log('has save', !!items[0].querySelector('.save-btn'));
  items[0].querySelector('.save-btn').dispatchEvent(new dom.window.Event('click'));
  await new Promise(res => setImmediate(res));
  assert.ok(putCalled, 'PUT should be called when saving edit');

  console.log('ExpenseForm tests passed');
}

run();
