document.addEventListener('DOMContentLoaded', () => {
  const acctForm = document.getElementById('account-form');
  const acctInputs = acctForm.querySelectorAll('input');
  document.getElementById('edit-account-btn')
    .addEventListener('click', () => {
      acctForm.classList.remove('read-only');
      acctInputs.forEach(i => i.removeAttribute('disabled'));
    });
  document.getElementById('cancel-account-btn')
    .addEventListener('click', () => {
      acctForm.classList.add('read-only');
      acctInputs.forEach(i => i.setAttribute('disabled', 'disabled'));
    });

  document.getElementById('edit-security-btn')
    .addEventListener('click', e => {
      e.preventDefault();
      document.getElementById('security-summary').classList.add('hidden');
      document.getElementById('security-form').classList.remove('hidden');
    });
  document.getElementById('cancel-security-btn')
    .addEventListener('click', () => {
      document.getElementById('security-form').classList.add('hidden');
      document.getElementById('security-summary').classList.remove('hidden');
    });

  let selectedAmount = null;
  document.querySelectorAll('.amount-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      selectedAmount = btn.dataset.amount;
      document.querySelectorAll('.amount-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById('custom-amount').value = '';
    });
  });

  document.getElementById('custom-amount').addEventListener('input', (e) => {
    selectedAmount = e.target.value;
    document.querySelectorAll('.amount-btn').forEach(b => b.classList.remove('active'));
  });

  document.getElementById('apply-topup-btn').addEventListener('click', async () => {
    const amount = parseInt(selectedAmount);
    const feedback = document.getElementById('topup-feedback');

    if (!amount || amount < 1) {
      feedback.textContent = '❗ Please select or enter a valid amount (min $1)';
      feedback.classList.remove('hidden');
      feedback.classList.add('error');
      return;
    }

    try {
      window.location.href = "/top-up?amount=" + amount;
    } catch (error) {
      console.error(error);
      feedback.textContent = '❌ Failed to start payment. Please try again.';
      feedback.classList.remove('hidden');
      feedback.classList.add('error');
    }
  });

  const plotData = [{
    values: [
      parseInt(document.getElementById('usageChart').dataset.inuse || 0),
      parseInt(document.getElementById('usageChart').dataset.returned || 0),
      parseInt(document.getElementById('usageChart').dataset.canceled || 0),
      parseInt(document.getElementById('usageChart').dataset.waiting || 0)
    ],
    labels: ['In-Use', 'Returned', 'Canceled', 'Waiting'],
    type: 'pie',
    hole: 0.5,
    marker: {
      colors: ['#88BDF2', '#2E5902', '#E39A7B', '#DBB06B']
    }
  }];
  const plotLayout = {
    title: 'Booking Activity',
    showlegend: false,
    margin: { t: 30, b: 20 }
  };
  Plotly.newPlot('usageChart', plotData, plotLayout, {
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['zoom', 'pan', 'select', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d']
  });

  setTimeout(() => {
    document.querySelectorAll('.error-message, .success-message').forEach(el => {
      el.style.transition = "opacity 0.5s ease";
      el.style.opacity = "0";
      setTimeout(() => el.remove(), 500);
    });
  }, 30000);
});
function togglePassword(inputId, iconId) {
  const input = document.getElementById(inputId);
  const icon = document.getElementById(iconId);

  const isHidden = input.type === "password";
  input.type = isHidden ? "text" : "password";

  icon.innerHTML = isHidden
    ? `<path d='M10 12a2 2 0 1 0 4 0a2 2 0 0 0 -4 0'/><path d='M21 12c-2.4 4 -5.4 6 -9 6c-3.6 0 -6.6 -2 -9 -6c2.4 -4 5.4 -6 9 -6c3.6 0 6.6 2 9 6'/>`
    : `<path d='M10.585 10.587a2 2 0 0 0 2.829 2.828'/><path d='M16.681 16.673a8.717 8.717 0 0 1 -4.681 1.327c-3.6 0 -6.6 -2 -9 -6c1.272 -2.12 2.712 -3.678 4.32 -4.674m2.86 -1.146a9.055 9.055 0 0 1 1.82 -.18c3.6 0 6.6 2 9 6c-.666 1.11 -1.379 2.067 -2.138 2.87'/><path d='M3 3l18 18'/>`;
 }
