import assert from 'assert';
import { JSDOM } from 'jsdom';
import IncomeForm from '../frontend/components/IncomeForm.js';

/**
 * Integration tests for the IncomeForm component.
 */
async function run() {
  const records = [
    { id: 1, amount: 100, description: 'A', created_at: Date.parse('2024-05-01') / 1000, target_month: '2024-05' },
    { id: 2, amount: 200, description: 'B', created_at: Date.parse('2024-05-10') / 1000, target_month: '2024-05' },
    { id: 3, amount: 300, description: 'C', created_at: Date.parse('2024-06-01') / 1000, target_month: '2024-06' }
  ];
  let postCalled = false;
  let putCalled = false;
  let deleteCalled = false;
  global.fetch = async (url, opts) => {
    if (url === '/incomes' && (!opts || opts.method === 'GET')) {
      return { json: async () => records };
    }
    if (url === '/incomes' && opts && opts.method === 'POST') { postCalled = true; return { ok: true }; }
    if (url.startsWith('/incomes/') && opts && opts.method === 'PUT') { putCalled = true; return { ok: true }; }
    if (url.startsWith('/incomes/') && opts && opts.method === 'DELETE') { deleteCalled = true; return { ok: true }; }
    throw new Error('unknown url');
  };

  const dom = new JSDOM('<!DOCTYPE html><body></body>', { url: 'http://localhost' });
  global.document = dom.window.document;
  global.window = dom.window;

  const el = IncomeForm();
  dom.window.document.body.appendChild(el);
  await new Promise(res => setImmediate(res));

  const monthInput = el.querySelector('input[type="month"]');
  monthInput.value = '2024-05';
  monthInput.dispatchEvent(new dom.window.Event('change'));
  await el.renderPromise;
  const items = el.querySelectorAll('ul li');
  assert.strictEqual(items.length, 2, 'Should show two records for selected month');

  const form = el.querySelector('form');
  const [amountInput, descInput] = form.querySelectorAll('input');
  descInput.dispatchEvent(new dom.window.Event('focus'));
  await new Promise(res => setImmediate(res));
  let autoList = form.querySelector('ul');
  assert.strictEqual(autoList.children.length, 3, 'Autocomplete should list past descriptions');
  descInput.value = 'B';
  descInput.dispatchEvent(new dom.window.Event('input'));
  await new Promise(res => setImmediate(res));
  assert.strictEqual(autoList.children.length, 1, 'Autocomplete should filter by substring');
  amountInput.value = 500;
  descInput.value = 'test';
  form.dispatchEvent(new dom.window.Event('submit'));
  await new Promise(res => setImmediate(res));
  assert.ok(postCalled, 'POST should be called when submitting new income');

  items[0].querySelector('.edit-btn').click();
  await new Promise(res => setImmediate(res));
  items[0].querySelector('.save-btn').dispatchEvent(new dom.window.Event('click'));
  await new Promise(res => setImmediate(res));
  assert.ok(putCalled, 'PUT should be called when saving edit');

  global.window.confirm = () => true;
  items[1].querySelector('.delete-btn').dispatchEvent(new dom.window.Event('click'));
  await new Promise(res => setImmediate(res));
  assert.ok(deleteCalled, 'DELETE should be called when deleting record');

  console.log('IncomeForm tests passed');
}

run();
