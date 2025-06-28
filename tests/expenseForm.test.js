import assert from 'assert';
import { JSDOM } from 'jsdom';
import ExpenseForm from '../frontend/components/ExpenseForm.js';

/**
 * Tests for the ExpenseForm component.
 */
async function run() {
  const dom = new JSDOM('<!DOCTYPE html><body></body>', { url: 'http://localhost' });
  global.document = dom.window.document;
  global.window = dom.window;
  let fetchCalled = false;
  global.fetch = (url, opts) => {
    fetchCalled = true;
    assert.strictEqual(url, '/expenses');
    assert.strictEqual(opts.method, 'POST');
    const data = JSON.parse(opts.body);
    assert.strictEqual(data.amount, 1000);
    assert.strictEqual(data.description, 'coffee');
    return Promise.resolve({ ok: true });
  };

  const formEl = ExpenseForm();
  dom.window.document.body.appendChild(formEl);
  const [amountInput, descInput] = formEl.querySelectorAll('input');
  amountInput.value = 1000;
  descInput.value = 'coffee';

  const submitEvent = new dom.window.Event('submit');
  formEl.querySelector('form').dispatchEvent(submitEvent);
  await new Promise(res => setImmediate(res));

  assert.ok(fetchCalled, 'fetch should be called on submit');
  console.log('ExpenseForm tests passed');
}

run();
