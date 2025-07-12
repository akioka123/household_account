import NavBar from './NavBar.js';
import { formatAmount } from '../utils/format.js';
import {
  fetchExpenses,
  createExpense,
  updateExpense,
  deleteExpense
} from '../api/expensesAPI.js';

/**
 * Build a list item element representing an expense.
 *
 * @param {object} expense - Expense object.
 * @param {Function} onEdit - Click handler for the edit button.
 * @param {Function} onDelete - Click handler for the delete button.
 * @returns {HTMLLIElement} Generated list element.
 */
function createExpenseItem(expense, onEdit, onDelete) {
  const li = document.createElement('li');
  li.className = 'bg-white p-3 shadow rounded flex justify-between items-center';

  const info = document.createElement('div');
  const pAmount = document.createElement('p');
  pAmount.textContent = `金額: ${formatAmount(expense.amount)}`;
  const pDesc = document.createElement('p');
  pDesc.textContent = `内容: ${expense.description}`;
  const pDate = document.createElement('p');
  pDate.textContent = `日付: ${new Date(expense.created_at * 1000).toLocaleDateString()}`;
  info.append(pAmount, pDesc, pDate);

  const editBtn = document.createElement('button');
  editBtn.textContent = '編集';
  editBtn.className = 'edit-btn bg-yellow-500 text-white px-3 py-1 rounded';

  const delBtn = document.createElement('button');
  delBtn.textContent = '削除';
  delBtn.className = 'delete-btn bg-red-500 text-white px-3 py-1 rounded ml-2';

  editBtn.addEventListener('click', onEdit);
  delBtn.addEventListener('click', onDelete);

  li.append(info, editBtn, delBtn);
  return li;
}

/**
 * Replace the list item with inline editing controls.
 *
 * @param {HTMLLIElement} li - Target list item.
 * @param {object} expense - Expense data to pre-fill.
 * @param {Function} onSave - Callback when save is clicked.
 * @param {Function} onCancel - Callback when cancel is clicked.
 */
function showEditForm(li, expense, onSave, onCancel) {
  li.innerHTML = `
    <div class="flex flex-col space-y-2 w-full">
      <input type="number" class="edit-amount border p-2" value="${expense.amount}">
      <input type="text" class="edit-description border p-2" value="${expense.description}">
      <input type="month" class="edit-month border p-2" value="${expense.target_month}">
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
 * Expense page component providing registration and list editing in one screen.
 * The layout mirrors the income screen.
 * @module ExpenseForm
 */
export default function ExpenseForm() {
  const container = document.createElement('div');
  container.className = 'min-h-screen flex flex-col items-center p-4 bg-gray-50';
  container.appendChild(NavBar('支出登録'));

  // Month selection using a calendar style input
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
  container.appendChild(form);

  const expenseListContainer = document.createElement('div');
  expenseListContainer.className = 'w-full max-w-5xl mt-4';
  container.appendChild(expenseListContainer);

  let renderSeq = 0;
  let renderPromise = Promise.resolve();
  container.renderPromise = renderPromise;
  const renderExpenseList = async (ym) => {
    const seq = ++renderSeq;
    expenseListContainer.innerHTML = '';
    const expenses = await fetchExpenses();
    const filtered = expenses.filter((e) => e.target_month === ym);

    if (filtered.length === 0) {
      expenseListContainer.textContent = 'この月には支出がありません。';
      return;
    }

    const ul = document.createElement('ul');
    ul.className = 'grid gap-2 grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5';
    filtered.slice(0, 25).forEach((expense) => {
      const li = createExpenseItem(
        expense,
        () => {
          renderSeq++; // cancel pending renders to keep edit form visible
          showEditForm(li, expense, async (updated) => {
            await updateExpense(expense.id, updated.amount, updated.description, updated.month);
            renderExpenseList(monthInput.value);
          }, () => renderExpenseList(monthInput.value));
        },
        async () => {
          if (window.confirm('削除してよろしいですか？')) {
            await deleteExpense(expense.id);
            renderExpenseList(monthInput.value);
          }
        }
      );
      ul.appendChild(li);
    });
    if (seq !== renderSeq) return;
    expenseListContainer.appendChild(ul);
  };

  // Update list when month input changes
  monthInput.addEventListener('change', () => {
    renderPromise = renderPromise.then(() => renderExpenseList(monthInput.value));
    container.renderPromise = renderPromise;
  });

  // Initial render of expense list
  renderPromise = renderExpenseList(monthInput.value);
  container.renderPromise = renderPromise;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const amount = Number(amountInput.value);
    const description = descInput.value;
    await createExpense(amount, description, monthInput.value);
    amountInput.value = '';
    descInput.value = '';
    renderExpenseList(monthInput.value);
  });


  const backLink = document.createElement('a');
  backLink.href = '#';
  backLink.textContent = '戻る';
  backLink.className = 'text-blue-600 underline mt-4';
  container.appendChild(backLink);

  return container;
}
