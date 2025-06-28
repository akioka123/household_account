import assert from 'assert';
import { JSDOM } from 'jsdom';
import ExpensesList from '../frontend/components/ExpensesList.js';

/**
 * Tests for the ExpensesList component.
 */
async function run() {
  const records = [
    { id: 1, amount: 100, description: 'A', created_at: Date.parse('2024-05-01') / 1000 },
    { id: 2, amount: 200, description: 'B', created_at: Date.parse('2024-05-10') / 1000 },
    { id: 3, amount: 300, description: 'C', created_at: Date.parse('2024-06-01') / 1000 }
  ];
  let putCalled = false;
  global.fetch = async (url, opts) => {
    if (url === '/expenses') return { json: async () => records };
    if (url.startsWith('/expenses/') && opts && opts.method === 'PUT') { putCalled = true; return { ok: true }; }
    throw new Error('unknown url');
  };

  const dom = new JSDOM('<!DOCTYPE html><body><div id="root"></div></body>', { url: 'http://localhost' });
  global.document = dom.window.document;
  global.window = dom.window;

  const el = await ExpensesList();
  dom.window.document.body.appendChild(el);
  const monthInput = el.querySelector('input[type="month"]');
  monthInput.value = '2024-05';
  monthInput.dispatchEvent(new dom.window.Event('change'));
  await new Promise(res => setImmediate(res));
  const rows = el.querySelectorAll('tbody tr');
  assert.strictEqual(rows.length, 2, 'Should show two records for selected month');

  rows[0].querySelector('.save').dispatchEvent(new dom.window.Event('click'));
  await new Promise(res => setImmediate(res));
  assert.ok(putCalled, 'PUT should be called when saving');
  console.log('ExpensesList tests passed');
}

run();
