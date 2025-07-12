import NavBar from './NavBar.js';
import { formatAmount } from '../utils/format.js';
import {
  fetchCashStart,
  registerCashStartAPI,
  fetchWithdrawals,
  createWithdrawal
} from '../api/cashAPI.js';

/**
 * Cash management page for tracking start amounts and withdrawals.
 * @module CashForm
 */
export default function CashForm() {
  const container = document.createElement('div');
  container.className = 'min-h-screen flex flex-col items-center p-4 bg-gray-50';
  container.appendChild(NavBar('現金管理'));

  const now = new Date();
  const monthInput = document.createElement('input');
  monthInput.type = 'month';
  monthInput.value = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2,'0')}`;
  monthInput.className = 'border p-2 mb-4';
  container.appendChild(monthInput);

  const startForm = document.createElement('form');
  startForm.className = 'flex flex-row space-x-2 w-full max-w-5xl mb-4';
  const startInput = document.createElement('input');
  startInput.type = 'number';
  startInput.placeholder = '月初額';
  startInput.className = 'border p-2 flex-1';
  const startBtn = document.createElement('button');
  startBtn.type = 'submit';
  startBtn.textContent = '月初額登録';
  startBtn.className = 'bg-blue-600 text-white p-2';
  startForm.append(startInput, startBtn);
  container.appendChild(startForm);

  const withdrawForm = document.createElement('form');
  withdrawForm.className = 'flex flex-row space-x-2 w-full max-w-5xl mb-4';
  const withdrawInput = document.createElement('input');
  withdrawInput.type = 'number';
  withdrawInput.placeholder = '出金額';
  withdrawInput.className = 'border p-2 flex-1';
  const withdrawBtn = document.createElement('button');
  withdrawBtn.type = 'submit';
  withdrawBtn.textContent = '出金追加';
  withdrawBtn.className = 'bg-blue-600 text-white p-2';
  withdrawForm.append(withdrawInput, withdrawBtn);
  container.appendChild(withdrawForm);

  const listContainer = document.createElement('div');
  listContainer.className = 'w-full max-w-5xl mt-4';
  container.appendChild(listContainer);

  const loadStart = async () => {
    const [y, m] = monthInput.value.split('-');
    const data = await fetchCashStart(y, m);
    if (data && data.amount !== undefined) {
      startInput.value = data.amount;
    } else {
      startInput.value = '';
    }
  };

  const loadWithdrawals = async () => {
    listContainer.innerHTML = '';
    const [y, m] = monthInput.value.split('-');
    const data = await fetchWithdrawals(y, m);
    if (data.length === 0) {
      listContainer.textContent = 'この月の出金記録はありません。';
      return;
    }
    const ul = document.createElement('ul');
    data.forEach(w => {
      const li = document.createElement('li');
      li.textContent = formatAmount(w.amount);
      ul.appendChild(li);
    });
    listContainer.appendChild(ul);
  };

  monthInput.addEventListener('change', () => {
    loadStart();
    loadWithdrawals();
  });

  startForm.addEventListener('submit', async e => {
    e.preventDefault();
    await registerCashStartAPI(monthInput.value, Number(startInput.value));
  });

  withdrawForm.addEventListener('submit', async e => {
    e.preventDefault();
    await createWithdrawal(monthInput.value, Number(withdrawInput.value));
    withdrawInput.value = '';
    loadWithdrawals();
  });

  loadStart();
  loadWithdrawals();

  return container;
}

