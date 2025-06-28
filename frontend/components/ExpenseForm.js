/**
 * Expense input form component for registering expenses via the backend API.
 * @module ExpenseForm
 */
export default function ExpenseForm() {
  const container = document.createElement('div');
  container.className = 'min-h-screen flex flex-col items-center p-4 bg-gray-50';

  const form = document.createElement('form');
  form.className = 'flex flex-col space-y-2 w-full max-w-sm';
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
  });

  container.appendChild(form);

  const backLink = document.createElement('a');
  backLink.href = '#';
  backLink.textContent = '戻る';
  backLink.className = 'text-blue-600 underline mt-4';
  container.appendChild(backLink);

  return container;
}
