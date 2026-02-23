from flask import Flask, render_template, request, jsonify
import math
import re
import hashlib

app = Flask(__name__)

# --- Password Analysis Logic (from analyzer.py, breach_check.py) ---
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

ROCKYOU_PATH = 'rockyou_sample.txt'

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

def check_dictionary(password, dict_path=ROCKYOU_PATH):
    try:
        with open(dict_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if password.lower() == line.strip().lower():
                    return True
    except Exception:
        pass
    return False

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

def check_breach_hash(password, breach_hash_path=ROCKYOU_PATH):
    try:
        hash_val = hashlib.sha256(password.encode('utf-8')).hexdigest()
        with open(breach_hash_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if hash_val == hashlib.sha256(line.strip().encode('utf-8')).hexdigest():
                    return True
    except Exception:
        pass
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

# --- Flask Routes ---
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    password = data.get("password", "")
    result = analyze_password(password)
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)
