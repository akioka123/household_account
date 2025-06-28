/**
 * ExpensesList component that displays expenses for a selected month and allows editing them.
 * @module ExpensesList
 */
import NavBar from './NavBar.js';

/**
 * Create the expenses list page element.
 * @returns {Promise<HTMLDivElement>} Root element containing the list
 */
export default async function ExpensesList() {
  const container = document.createElement('div');
  container.className = 'min-h-screen flex flex-col items-center p-4 bg-gray-50';
  container.appendChild(NavBar());

  const monthInput = document.createElement('input');
  monthInput.type = 'month';
  monthInput.className = 'border p-2';
  const now = new Date();
  monthInput.value = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  container.appendChild(monthInput);

  const table = document.createElement('table');
  table.className = 'min-w-full text-sm text-left border mt-4';
  table.innerHTML = '<thead><tr><th class="border px-2">日付</th><th class="border px-2">内容</th><th class="border px-2">金額</th><th class="border px-2">保存</th></tr></thead><tbody></tbody>';
  container.appendChild(table);

  async function load() {
    const res = await fetch('/expenses');
    const data = await res.json();
    const [y, m] = monthInput.value.split('-').map(Number);
    const tbody = table.querySelector('tbody');
    tbody.innerHTML = '';
    data.filter((e) => {
      const d = new Date(e.created_at * 1000);
      return d.getFullYear() === y && d.getMonth() + 1 === m;
    }).forEach((e) => {
      const tr = document.createElement('tr');
      const date = new Date(e.created_at * 1000).toLocaleDateString();
      tr.innerHTML = `<td class="border px-2">${date}</td>` +
        `<td class="border px-2"><input class="desc border p-1" type="text" value="${e.description || ''}"></td>` +
        `<td class="border px-2"><input class="amount border p-1 text-right" type="number" value="${e.amount}"></td>` +
        '<td class="border px-2"><button class="save bg-blue-600 text-white px-2">保存</button></td>';
      tr.querySelector('.save').addEventListener('click', async () => {
        const amount = Number(tr.querySelector('.amount').value);
        const description = tr.querySelector('.desc').value;
        await fetch(`/expenses/${e.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ amount, description })
        });
        await load();
      });
      tbody.appendChild(tr);
    });
  }

  monthInput.addEventListener('change', load);
  await load();
  return container;
}
