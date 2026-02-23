document.addEventListener('DOMContentLoaded', function() {
  const form = document.getElementById('analyzeForm');
  const resultCard = document.getElementById('resultCard');
  const resultBody = document.getElementById('resultBody');
  const strengthBar = document.getElementById('strengthBar');
  const strengthLabel = document.getElementById('strengthLabel');
  const pwdInput = document.getElementById('password');
  const toggleBtn = document.getElementById('togglePwd');

  form.addEventListener('submit', async function(e) {
    e.preventDefault();
    const pwd = pwdInput.value;
    if (!pwd) return;
    resultCard.classList.remove('fade-in');
    resultBody.innerHTML = '<div class="text-center text-secondary">Analyzing...</div>';
    fetch('/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password: pwd })
    })
    .then(res => res.json())
    .then(data => {
      resultCard.classList.add('fade-in');
      let color = '#dc3545';
      if (data.level === 'Moderate') color = '#fd7e14';
      if (data.level === 'Strong') color = '#0d6efd';
      if (data.level === 'Very Strong') color = '#198754';
      strengthBar.style.width = data.score + '%';
      strengthBar.style.background = color;
      strengthLabel.textContent = data.level;
      strengthLabel.style.color = color;
      resultBody.innerHTML = `
        <div><b>Entropy:</b> ${data.entropy} bits</div>
        <div><b>Crack Time (Offline):</b> ${data.crack_time.offline}</div>
        <div><b>Crack Time (Online):</b> ${data.crack_time.online}</div>
        <div><b>Patterns:</b> ${data.patterns.length ? data.patterns.join(', ') : 'None'}</div>
        <div><b>Dictionary Match:</b> ${data.dict_match ? 'Yes' : 'No'}</div>
        <div><b>Breach Status:</b> ${data.breach ? 'Found' : 'Not Found'}</div>
        <div><b>Score:</b> ${data.score}</div>
      `;
    });
  });

  toggleBtn.addEventListener('click', function() {
    if (pwdInput.type === 'password') {
      pwdInput.type = 'text';
      toggleBtn.innerHTML = '<i class="bi bi-eye-slash"></i>';
    } else {
      pwdInput.type = 'password';
      toggleBtn.innerHTML = '<i class="bi bi-eye"></i>';
    }
  });
});
