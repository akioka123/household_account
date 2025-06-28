/**
 * Expense input form component for registering expenses via the backend API.
 * @module ExpenseForm
 */
export default function ExpenseForm() {
  const container = document.createElement('div');

  const form = document.createElement('form');
  const amountInput = document.createElement('input');
  amountInput.type = 'number';
  amountInput.placeholder = '金額';

  const descInput = document.createElement('input');
  descInput.type = 'text';
  descInput.placeholder = '内容';

  const submitBtn = document.createElement('button');
  submitBtn.type = 'submit';
  submitBtn.textContent = '登録';

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
  container.appendChild(backLink);

  return container;
}
