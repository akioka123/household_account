import NavBar from './NavBar.js';
import { formatAmount } from '../utils/format.js';
import {
  fetchIncomes,
  createIncome,
  updateIncome,
  deleteIncome
} from '../api/incomesAPI.js';

/**
 * Build a list item element representing an income.
 *
 * @param {object} income - Income object.
 * @param {Function} onEdit - Click handler for the edit button.
 * @param {Function} onDelete - Click handler for the delete button.
 * @returns {HTMLLIElement} Generated list element.
 */
function createIncomeItem(income, onEdit, onDelete) {
  const li = document.createElement('li');
  li.className = 'bg-white p-3 shadow rounded justify-between items-center';

  const info = document.createElement('div');
  info.className = 'grid grid-rows-2 md:grid-rows-3 grid-cols-2 md:grid-cols-1 gap-1 flex-1';
  const pDesc = document.createElement('p');
  pDesc.textContent = `内容: ${income.description}`;
  const pAmount = document.createElement('p');
  pAmount.textContent = `金額: ${formatAmount(income.amount)}`;
  const pDate = document.createElement('p');
  pDate.textContent = `日付: ${new Date(income.created_at * 1000).toLocaleDateString()}`;
  info.append(pDesc, pAmount, pDate);

  const btns = document.createElement('div');
  btns.className = 'grid grid-rows-1 grid-cols-2 gap-1 flex-1 mt-2';
  const editBtn = document.createElement('button');
  editBtn.textContent = '編集';
  editBtn.className = 'edit-btn bg-yellow-500 text-white px-1 py-1 rounded';

  const delBtn = document.createElement('button');
  delBtn.textContent = '削除';
  delBtn.className = 'delete-btn bg-red-500 text-white px-1 py-1 rounded';

  editBtn.addEventListener('click', onEdit);
  delBtn.addEventListener('click', onDelete);

  btns.append(editBtn, delBtn);
  li.append(info, btns);
  return li;
}

/**
 * Replace the list item with inline editing controls for incomes.
 *
 * @param {HTMLLIElement} li - Target list item.
 * @param {object} income - Income data to pre-fill.
 * @param {Function} onSave - Callback when save is clicked.
 * @param {Function} onCancel - Callback when cancel is clicked.
 */
function showEditForm(li, income, onSave, onCancel) {
  li.innerHTML = `
    <div class="flex flex-col space-y-2 w-full">
      <input type="number" class="edit-amount border p-2" value="${income.amount}">
      <input type="text" class="edit-description border p-2" value="${income.description}">
      <input type="month" class="edit-month border p-2" value="${income.target_month}">
      <div class="flex space-x-2">
        <button class="save-btn bg-green-500 text-white px-3 py-1 rounded">保存</button>
        <button class="cancel-btn bg-gray-500 text-white px-3 py-1 rounded">キャンセル</button>
      </div>
    </div>`;

  li.querySelector('.save-btn').addEventListener('click', () => {
    const newAmount = Number(li.querySelector('.edit-amount').value);
    const newDescription = li.querySelector('.edit-description').value;
    const newMonth = li.querySelector('.edit-month').value;
    onSave({ amount: newAmount, description: newDescription, month: newMonth });
  });

  li.querySelector('.cancel-btn').addEventListener('click', onCancel);
}

/**
 * Attach autocomplete functionality using past income descriptions.
 *
 * @param {HTMLInputElement} input - Target description input.
 */
function setupAutocomplete(input) {
  const wrapper = input.parentElement;
  wrapper.style.position = 'relative';

  const list = document.createElement('ul');
  list.className =
    'absolute left-0 right-0 bg-white border mt-1 max-h-40 overflow-y-auto z-10 hidden';
  wrapper.appendChild(list);

  let descriptions = [];

  const filter = () => {
    list.innerHTML = '';
    const query = input.value.trim();
    const items = descriptions.filter((d) => d.includes(query));
    if (items.length === 0) {
      list.classList.add('hidden');
      return;
    }
    items.forEach((d) => {
      const li = document.createElement('li');
      li.textContent = d;
      li.className = 'px-2 py-1 cursor-pointer hover:bg-gray-100';
      li.addEventListener('mousedown', () => {
        input.value = d;
        list.classList.add('hidden');
      });
      list.appendChild(li);
    });
    list.classList.remove('hidden');
  };

  const load = async () => {
    const incomes = await fetchIncomes();
    const uniq = new Set();
    incomes.forEach((i) => {
      if (i.description) uniq.add(i.description);
    });
    descriptions = Array.from(uniq);
    filter();
  };

  input.addEventListener('focus', load);
  input.addEventListener('input', filter);
  input.addEventListener('blur', () =>
    setTimeout(() => list.classList.add('hidden'), 100)
  );
}

/**
 * Income page component providing registration and list editing in one screen.
 * Mirrors the expense screen implementation.
 * @module IncomeForm
 */
export default function IncomeForm() {
  const container = document.createElement('div');
  container.className = 'min-h-screen flex flex-col items-center p-4 bg-gray-50';
  container.appendChild(NavBar('収入登録'));

  const now = new Date();
  const monthInput = document.createElement('input');
  monthInput.type = 'month';
  monthInput.value = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  monthInput.className = 'border p-2 mb-4';
  container.appendChild(monthInput);

  const form = document.createElement('form');
  form.className = 'flex flex-row space-x-2 w-full max-w-5xl mb-4';
  const amountInput = document.createElement('input');
  amountInput.type = 'number';
  amountInput.placeholder = '金額';
  amountInput.className = 'border p-2 flex-1';

  const descInput = document.createElement('input');
  descInput.type = 'text';
  descInput.placeholder = '内容';
  descInput.className = 'border p-2 flex-1';

  const submitBtn = document.createElement('button');
  submitBtn.type = 'submit';
  submitBtn.textContent = '登録';
  submitBtn.className = 'bg-blue-600 text-white p-2';

  form.appendChild(amountInput);
  form.appendChild(descInput);
  form.appendChild(submitBtn);
  setupAutocomplete(descInput);
  container.appendChild(form);

  const incomeListContainer = document.createElement('div');
  incomeListContainer.className = 'w-full max-w-5xl mt-4';
  container.appendChild(incomeListContainer);

  let renderSeq = 0;
  let renderPromise = Promise.resolve();
  container.renderPromise = renderPromise;
  const renderIncomeList = async (ym) => {
    const seq = ++renderSeq;
    incomeListContainer.innerHTML = '';
    const incomes = await fetchIncomes();
    const filtered = incomes.filter((i) => i.target_month === ym);

    if (filtered.length === 0) {
      incomeListContainer.textContent = 'この月には収入がありません。';
      return;
    }

    const ul = document.createElement('ul');
    ul.className = 'grid gap-2 grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5';
    filtered.slice(0, 25).forEach((income) => {
      const li = createIncomeItem(
        income,
        () => {
          renderSeq++;
          showEditForm(li, income, async (updated) => {
            await updateIncome(income.id, updated.amount, updated.description, updated.month);
            renderIncomeList(monthInput.value);
          }, () => renderIncomeList(monthInput.value));
        },
        async () => {
          if (window.confirm('削除してよろしいですか？')) {
            await deleteIncome(income.id);
            renderIncomeList(monthInput.value);
          }
        }
      );
      ul.appendChild(li);
    });
    if (seq !== renderSeq) return;
    incomeListContainer.appendChild(ul);
  };

  monthInput.addEventListener('change', () => {
    renderPromise = renderPromise.then(() => renderIncomeList(monthInput.value));
    container.renderPromise = renderPromise;
  });

  renderPromise = renderIncomeList(monthInput.value);
  container.renderPromise = renderPromise;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const amount = Number(amountInput.value);
    const description = descInput.value;
    await createIncome(amount, description, monthInput.value);
    amountInput.value = '';
    descInput.value = '';
    renderIncomeList(monthInput.value);
  });

  return container;
}
