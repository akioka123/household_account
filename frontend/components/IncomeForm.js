import NavBar from './NavBar.js';
import { formatAmount } from '../utils/format.js';

/**
 * Income input form component for registering incomes via the backend API.
 * @module IncomeForm
 */
export default function IncomeForm() {
  const container = document.createElement('div');
  container.className = 'min-h-screen flex flex-col items-center p-4 bg-gray-50';
  container.appendChild(NavBar('収入登録'));

  // Month selection using calendar component
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

  const incomeListContainer = document.createElement('div');
  incomeListContainer.className = 'w-full max-w-5xl mt-4';
  container.appendChild(incomeListContainer);

  let renderPromise = Promise.resolve();
  container.renderPromise = renderPromise;

  const renderIncomeList = async (ym) => {
    incomeListContainer.innerHTML = ''; // Clear previous list
    const [year, month] = ym.split('-').map(Number);
    const response = await fetch(`/incomes/month/${year}/${month}`);
    const incomes = await response.json();

    if (incomes.length === 0) {
      incomeListContainer.textContent = 'この月には収入がありません。';
      return;
    }

    const ul = document.createElement('ul');
    ul.className = 'grid gap-2 grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5';
    incomes.slice(0, 25).forEach(income => {
      const li = document.createElement('li');
      li.className = 'bg-white p-3 shadow rounded flex justify-between items-center';
      li.innerHTML = `
        <div>
          <p>金額: ${formatAmount(income.amount)}</p>
          <p>内容: ${income.description}</p>
          <p>日付: ${new Date(income.created_at * 1000).toLocaleDateString()}</p>
        </div>
        <button data-id="${income.id}" data-amount="${income.amount}" data-description="${income.description}" data-month="${income.target_month}" class="edit-btn bg-yellow-500 text-white px-3 py-1 rounded">編集</button>
        <button data-id="${income.id}" class="delete-btn bg-red-500 text-white px-3 py-1 rounded ml-2">削除</button>
      `;
      ul.appendChild(li);
    });
    incomeListContainer.appendChild(ul);

    // Add event listeners for edit buttons
    ul.querySelectorAll('.edit-btn').forEach(button => {
      button.addEventListener('click', (e) => {
        const id = e.target.dataset.id;
        const currentAmount = e.target.dataset.amount;
        const currentDescription = e.target.dataset.description;
        const currentMonth = e.target.dataset.month;
        
        const listItem = e.target.closest('li');
        listItem.innerHTML = `
          <div class="flex flex-col space-y-2 w-full">
            <input type="number" class="edit-amount border p-2" value="${currentAmount}">
            <input type="text" class="edit-description border p-2" value="${currentDescription}">
            <input type="month" class="edit-month border p-2" value="${currentMonth}">
            <div class="flex space-x-2">
              <button data-id="${id}" class="save-btn bg-green-500 text-white px-3 py-1 rounded">保存</button>
              <button class="cancel-btn bg-gray-500 text-white px-3 py-1 rounded">キャンセル</button>
            </div>
          </div>
        `;

        listItem.querySelector('.save-btn').addEventListener('click', async (saveEvent) => {
          const newAmount = listItem.querySelector('.edit-amount').value;
          const newDescription = listItem.querySelector('.edit-description').value;
          const newMonth = listItem.querySelector('.edit-month').value;
          await fetch(`/incomes/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ amount: Number(newAmount), description: newDescription, targetMonth: newMonth })
          });
          renderIncomeList(monthInput.value); // Re-render after save
        });

        listItem.querySelector('.cancel-btn').addEventListener('click', () => {
          renderIncomeList(monthInput.value); // Re-render to revert changes
        });
      });
    });
    ul.querySelectorAll('.delete-btn').forEach(button => {
      button.addEventListener('click', async (e) => {
        const id = e.target.dataset.id;
        if (window.confirm('削除してよろしいですか？')) {
          await fetch(`/incomes/${id}`, { method: 'DELETE' });
          renderIncomeList(monthInput.value);
        }
      });
    });
  };

  // Update list when month input changes
  monthInput.addEventListener('change', () => {
    renderPromise = renderPromise.then(() => renderIncomeList(monthInput.value));
    container.renderPromise = renderPromise;
  });

  // Initial render
  renderPromise = renderIncomeList(monthInput.value);
  container.renderPromise = renderPromise;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const amount = Number(amountInput.value);
    const description = descInput.value;
    await fetch('/incomes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount, description, targetMonth: monthInput.value })
    });
    amountInput.value = '';
    descInput.value = '';
    renderIncomeList(monthInput.value); // Re-render after new income added
  });

  return container;
}
