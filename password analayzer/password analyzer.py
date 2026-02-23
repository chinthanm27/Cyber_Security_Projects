import math
import re
import hashlib
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# --- Password Analysis Logic ---
KEYBOARD_PATTERNS = [
    'qwerty', 'asdf', 'zxcv', '1234', 'qaz', 'wsx', 'edc', 'rfv', 'tgb', 'yhn', 'ujm', 'ik', 'ol', 'pl',
]
COMMON_NAMES = [
    'john', 'michael', 'david', 'james', 'robert', 'mary', 'patricia', 'jennifer', 'linda', 'elizabeth',
    'barbara', 'susan', 'jessica', 'sarah', 'ashley', 'bailey', 'charlie', 'daniel', 'emily', 'hannah',
]
CHAR_POOLS = [
    (r'[a-z]', 26),
    (r'[A-Z]', 26),
    (r'[0-9]', 10),
    (r'[^a-zA-Z0-9]', 32),
]
SEQUENTIAL_REGEX = r'(?:0123|1234|2345|3456|4567|5678|6789|7890|abcd|bcde|cdef|defg|efgh|fghi|ghij|hijk|ijkl|jklm|klmn|lmno|mnop|nopq|opqr|pqrs|qrst|rstu|stuv|tuvw|uvwx|vwxy|wxyz)'
REPEAT_REGEX = r'(.)\1{2,}'
YEAR_REGEX = r'19[9][0-9]|20[0-2][0-9]|202[0-5]'

ROCKYOU_SAMPLE = set([
    'password','123456','qwerty','letmein','welcome','admin','monkey','abc123','iloveyou','sunshine',
    'princess','football','charlie','michael','shadow','ashley','bailey','passw0rd','superman','batman','trustno1'
])

# --- Analysis Functions ---
def calculate_entropy(password):
    pool = 0
    for regex, size in CHAR_POOLS:
        if re.search(regex, password):
            pool += size
    if pool == 0:
        pool = 1
    entropy = len(password) * math.log2(pool)
    return round(entropy, 2), pool

def estimate_crack_time(password, pool):
    guesses = pool ** len(password)
    offline = guesses / 1e10
    online = guesses / 1e3
    def format_time(seconds):
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        y, d = divmod(d, 365)
        return f"{int(seconds):,} sec | {int(m):,} min | {int(h):,} hr | {int(d):,} d | {int(y):,} yr"
    return {
        'offline': format_time(offline),
        'online': format_time(online),
        'offline_raw': offline,
        'online_raw': online
    }

def check_dictionary(password):
    return password.lower() in ROCKYOU_SAMPLE

def detect_patterns(password):
    patterns = []
    if re.search(SEQUENTIAL_REGEX, password.lower()):
        patterns.append('Sequential pattern')
    for pat in KEYBOARD_PATTERNS:
        if pat in password.lower():
            patterns.append('Keyboard pattern')
            break
    if re.search(REPEAT_REGEX, password):
        patterns.append('Repeated characters')
    if re.search(YEAR_REGEX, password):
        patterns.append('Common year')
    for name in COMMON_NAMES:
        if name in password.lower():
            patterns.append('Common name')
            break
    return patterns

def check_breach_hash(password):
    hash_val = hashlib.sha256(password.encode('utf-8')).hexdigest()
    for word in ROCKYOU_SAMPLE:
        if hash_val == hashlib.sha256(word.encode('utf-8')).hexdigest():
            return True
    return False

def score_password(password, entropy, dict_match, patterns):
    score = 50
    if entropy < 40:
        score -= 20
    elif entropy < 60:
        score -= 10
    else:
        score += 10
    if len(password) > 12:
        score += 10
    types = sum(bool(re.search(regex, password)) for regex, _ in CHAR_POOLS)
    if types >= 3:
        score += 10
    if dict_match:
        score -= 30
    if patterns:
        score -= 10 * len(patterns)
    score = max(0, min(100, score))
    return score

def strength_level(score):
    if score < 30:
        return 'Weak'
    elif score < 60:
        return 'Moderate'
    elif score < 80:
        return 'Strong'
    else:
        return 'Very Strong'

def analyze_password(password):
    entropy, pool = calculate_entropy(password)
    crack = estimate_crack_time(password, pool)
    dict_match = check_dictionary(password)
    patterns = detect_patterns(password)
    breach = check_breach_hash(password)
    score = score_password(password, entropy, dict_match, patterns)
    level = strength_level(score)
    return {
        'entropy': entropy,
        'crack_time': crack,
        'patterns': patterns,
        'dict_match': dict_match,
        'breach': breach,
        'score': score,
        'level': level
    }

# --- HTML Template ---
HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Password Strength Analyzer</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css" rel="stylesheet">
  <style>
    body { background: #181c20; color: #f8f9fa; font-family: 'Segoe UI', Arial, sans-serif; }
    .card { background: #23272b; border-radius: 1rem; box-shadow: 0 4px 24px rgba(0,0,0,0.2); border: none; }
    #strengthBar { transition: width 0.7s cubic-bezier(.4,2,.6,1), background 0.5s; height: 1.5rem; border-radius: 0.75rem; }
    .fade-in { animation: fadeIn 1s; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: none; } }
  </style>
</head>
<body>
  <div class="container py-5">
    <div class="row justify-content-center">
      <div class="col-md-7">
        <div class="card p-4 mb-4 shadow-lg">
          <h2 class="mb-3 text-center">🔒 Advanced Password Strength Analyzer</h2>
          <form id="analyzeForm" autocomplete="off">
            <div class="input-group mb-3">
              <input type="password" class="form-control form-control-lg" id="password" placeholder="Enter password" required>
              <button class="btn btn-outline-secondary" type="button" id="togglePwd" tabindex="-1"><i class="bi bi-eye"></i></button>
            </div>
            <button class="btn btn-primary w-100" type="submit">Analyze</button>
          </form>
        </div>
        <div class="card card-body mb-3 fade-in" id="resultCard" style="display:block;">
          <div class="mb-2">
            <div class="d-flex align-items-center mb-2">
              <div class="flex-grow-1 me-2">
                <div class="progress" style="height:1.5rem;">
                  <div id="strengthBar" class="progress-bar" style="width:0%"></div>
                </div>
              </div>
              <span id="strengthLabel" class="fw-bold ms-2"></span>
            </div>
          </div>
          <div id="resultBody" class="mt-2"></div>
        </div>
      </div>
    </div>
    <footer class="text-center mt-5 text-secondary small">&copy; 2026 Advanced Password Analyzer | Cybersecurity Project</footer>
  </div>
  <script>
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
  </script>
</body>
</html>
'''

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    password = data.get("password", "")
    result = analyze_password(password)
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)