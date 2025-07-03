import NavBar from './NavBar.js';
import { formatAmount } from '../utils/format.js';

/**
 * Expense page component providing registration and list editing in one screen.
 * The layout mirrors the income screen.
 * @module ExpenseForm
 */
export default function ExpenseForm() {
  const container = document.createElement('div');
  container.className = 'min-h-screen flex flex-col items-center p-4 bg-gray-50';
  container.appendChild(NavBar('支出登録'));

  // Month selection controls
  const monthSelectContainer = document.createElement('div');
  monthSelectContainer.className = 'mb-4';
  const yearSelect = document.createElement('select');
  const monthSelect = document.createElement('select');
  monthSelectContainer.appendChild(yearSelect);
  monthSelectContainer.appendChild(monthSelect);
  container.appendChild(monthSelectContainer);

  const expenseListContainer = document.createElement('div');
  expenseListContainer.className = 'w-full max-w-sm mt-4';
  container.appendChild(expenseListContainer);

  let renderSeq = 0;
  let renderPromise = Promise.resolve();
  container.renderPromise = renderPromise;
  const renderExpenseList = async (year, month) => {
    const seq = ++renderSeq;
    expenseListContainer.innerHTML = '';
    const res = await fetch('/expenses');
    const expenses = await res.json();
    const filtered = expenses.filter((e) => {
      const d = new Date(e.created_at * 1000);
      return d.getFullYear() === Number(year) && d.getMonth() + 1 === Number(month);
    });

    if (filtered.length === 0) {
      expenseListContainer.textContent = 'この月には支出がありません。';
      return;
    }

    const ul = document.createElement('ul');
    ul.className = 'space-y-2';
    filtered.forEach((expense) => {
      const li = document.createElement('li');
      li.className = 'bg-white p-3 shadow rounded flex justify-between items-center';
      li.innerHTML = `
        <div>
          <p>金額: ${formatAmount(expense.amount)}</p>
          <p>内容: ${expense.description}</p>
          <p>日付: ${new Date(expense.created_at * 1000).toLocaleDateString()}</p>
        </div>
        <button data-id="${expense.id}" data-amount="${expense.amount}" data-description="${expense.description}" class="edit-btn bg-yellow-500 text-white px-3 py-1 rounded">編集</button>
      `;
      ul.appendChild(li);
    });
    if (seq !== renderSeq) return;
    expenseListContainer.appendChild(ul);

    ul.querySelectorAll('.edit-btn').forEach((button) => {
      button.addEventListener('click', (e) => {
        renderSeq++; // cancel pending renders to keep edit form visible
        const id = e.target.dataset.id;
        const currentAmount = e.target.dataset.amount;
        const currentDescription = e.target.dataset.description;
        const listItem = e.target.closest('li');
        listItem.innerHTML = `
          <div class="flex flex-col space-y-2 w-full">
            <input type="number" class="edit-amount border p-2" value="${currentAmount}">
            <input type="text" class="edit-description border p-2" value="${currentDescription}">
            <div class="flex space-x-2">
              <button data-id="${id}" class="save-btn bg-green-500 text-white px-3 py-1 rounded">保存</button>
              <button class="cancel-btn bg-gray-500 text-white px-3 py-1 rounded">キャンセル</button>
            </div>
          </div>
        `;

        listItem.querySelector('.save-btn').addEventListener('click', async () => {
          const newAmount = listItem.querySelector('.edit-amount').value;
          const newDescription = listItem.querySelector('.edit-description').value;
          await fetch(`/expenses/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ amount: Number(newAmount), description: newDescription })
          });
          renderExpenseList(yearSelect.value, monthSelect.value);
        });

        listItem.querySelector('.cancel-btn').addEventListener('click', () => {
          renderExpenseList(yearSelect.value, monthSelect.value);
        });
      });
    });
  };

  // Populate year/month drop-downs
  const currentYear = new Date().getFullYear();
  const currentMonth = new Date().getMonth() + 1;
  for (let i = currentYear - 2; i <= currentYear + 1; i++) {
    const option = document.createElement('option');
    option.value = i;
    option.textContent = i;
    if (i === currentYear) option.selected = true;
    yearSelect.appendChild(option);
  }
  for (let i = 1; i <= 12; i++) {
    const option = document.createElement('option');
    option.value = i;
    option.textContent = i;
    if (i === currentMonth) option.selected = true;
    monthSelect.appendChild(option);
  }

  yearSelect.addEventListener('change', () => {
    renderPromise = renderPromise.then(() => renderExpenseList(yearSelect.value, monthSelect.value));
    container.renderPromise = renderPromise;
  });
  monthSelect.addEventListener('change', () => {
    renderPromise = renderPromise.then(() => renderExpenseList(yearSelect.value, monthSelect.value));
    container.renderPromise = renderPromise;
  });

  // Initial render of expense list
  renderPromise = renderExpenseList(currentYear, currentMonth);
  container.renderPromise = renderPromise;

  const form = document.createElement('form');
  form.className = 'flex flex-col space-y-2 w-full max-w-sm mt-8';
  const amountInput = document.createElement('input');
  amountInput.type = 'number';
  amountInput.placeholder = '金額';
  amountInput.className = 'border p-2';

  const descInput = document.createElement('input');
  descInput.type = 'text';
  descInput.placeholder = '内容';
  descInput.className = 'border p-2';

  const submitBtn = document.createElement('button');
  submitBtn.type = 'submit';
  submitBtn.textContent = '登録';
  submitBtn.className = 'bg-blue-600 text-white p-2';

  form.appendChild(amountInput);
  form.appendChild(descInput);
  form.appendChild(submitBtn);

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const amount = Number(amountInput.value);
    const description = descInput.value;
    await fetch('/expenses', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount, description })
    });
    amountInput.value = '';
    descInput.value = '';
    renderExpenseList(yearSelect.value, monthSelect.value);
  });

  container.appendChild(form);

  const backLink = document.createElement('a');
  backLink.href = '#';
  backLink.textContent = '戻る';
  backLink.className = 'text-blue-600 underline mt-4';
  container.appendChild(backLink);

  return container;
}
