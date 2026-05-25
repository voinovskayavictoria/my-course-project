from flask import Flask, send_from_directory, jsonify, request
import json
import os
import random
import re
from datetime import datetime
import torch
import pickle
import numpy as np

app = Flask(__name__, static_folder='.')

class APIFuzzerNet(torch.nn.Module):
    def __init__(self, vocab_size, embedding_dim, hidden_dim):
        super().__init__()
        self.embedding = torch.nn.Embedding(vocab_size, embedding_dim)
        self.lstm = torch.nn.LSTM(embedding_dim, hidden_dim, batch_first=True)
        self.fc = torch.nn.Linear(hidden_dim, vocab_size)

    def forward(self, x, hidden=None):
        x = self.embedding(x)
        x, hidden = self.lstm(x, hidden)
        x = self.fc(x)
        return x, hidden

with open("char_to_idx.pkl", "rb") as f:
    char_to_idx = pickle.load(f)
with open("idx_to_char.pkl", "rb") as f:
    idx_to_char = pickle.load(f)

vocab_size = len(char_to_idx)
SEQ_LENGTH = 30
DEFAULT_START = '{"method":"GET","url":"http://'
OUTPUT_JSONL = "generated_payloads.jsonl"
LEGIT_REQUESTS_PATH = "legitimate_requests.jsonl"
MAX_TEMPLATES = 5000

model = APIFuzzerNet(vocab_size, 64, 128)
model.load_state_dict(torch.load("api_fuzzer_model.pth", map_location='cpu'))
model.eval()
print(f"Модель загружена. Алфавит: {vocab_size} символов")

MUTATION_PAYLOADS = [
    "' OR 1=1 --",
    "<script>alert(1)</script>",
    "../../../etc/passwd",
    "%00",
    "{{7*7}}"
]

def _load_legit_templates(path, limit):
    templates = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            templates.append(json.loads(line))
            if len(templates) >= limit:
                break
    if not templates:
        raise ValueError("Не удалось загрузить легитимные шаблоны")
    return templates

LEGIT_TEMPLATES = _load_legit_templates(LEGIT_REQUESTS_PATH, MAX_TEMPLATES)

def _escape_json_string(value):
    return json.dumps(value, ensure_ascii=False)[1:-1]

def _normalize_start_str(start_str):
    if not start_str:
        return DEFAULT_START
    if start_str.strip() == '{"user_id":':
        return DEFAULT_START
    return start_str

def _append_mutation(start_str, payload):
    if not start_str.endswith('"'):
        start_str += '"'
    return start_str + _escape_json_string(payload)

def _extract_field_and_prefix(start_str):
    if not start_str:
        return "url", ""
    match = re.search(r'"([^"]+)"\s*:\s*"([^"]*)$', start_str)
    if match:
        return match.group(1), match.group(2)
    match = re.search(r'"([^"]+)"\s*:\s*$', start_str)
    if match:
        return match.group(1), ""
    return "url", ""

def _merge_prefix(prefix, base_value):
    base_value = base_value or ""
    if not prefix:
        return base_value
    if base_value.startswith(prefix):
        return base_value
    if re.match(r"^https?://", prefix):
        base_value = re.sub(r"^https?://", "", base_value)
        return prefix + base_value
    return prefix + base_value

def _inject_payload(value, payload):
    if not payload:
        return value
    if not value:
        return payload
    if value.endswith(("/", "?", "&", "=")):
        return value + payload
    if "?" in value:
        return value + "&" + payload
    return value + payload

def _has_unclosed_quote(text):
    in_str = False
    escape = False
    for ch in text:
        if escape:
            escape = False
            continue
        if ch == '\\' and in_str:
            escape = True
            continue
        if ch == '"':
            in_str = not in_str
    return in_str

def _repair_json(text):
    start = text.find('{')
    if start > 0:
        text = text[start:]

    if _has_unclosed_quote(text):
        text += '"'

    balance = 0
    in_str = False
    escape = False
    for ch in text:
        if escape:
            escape = False
            continue
        if ch == '\\' and in_str:
            escape = True
            continue
        if ch == '"':
            in_str = not in_str
            continue
        if not in_str:
            if ch == '{':
                balance += 1
            elif ch == '}':
                balance = max(balance - 1, 0)

    if balance > 0:
        text += '}' * balance

    last_brace = text.rfind('}')
    if last_brace != -1:
        text = text[:last_brace + 1]
    return text

def _parse_json_prefix(text):
    try:
        _, end = json.JSONDecoder().raw_decode(text)
        return text[:end]
    except json.JSONDecodeError:
        return None

def _append_jsonl(records, path):
    with open(path, "a", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

def generate_payload(start_str, temperature, length):
    input_indices = [char_to_idx.get(ch, char_to_idx['{']) for ch in start_str]
    hidden = None
    result = start_str
    
    
    for _ in range(length):
        if len(input_indices) >= SEQ_LENGTH:
            inp = torch.tensor([input_indices[-SEQ_LENGTH:]])
        else:
            pad = [char_to_idx['{']] * (SEQ_LENGTH - len(input_indices)) + input_indices
            inp = torch.tensor([pad])
        
        with torch.no_grad():
            out, hidden = model(inp, hidden)
        
        logits = out[0, -1, :] / temperature
        probs = torch.softmax(logits, dim=0).numpy()
        next_idx = np.random.choice(len(probs), p=probs)
        result += idx_to_char[next_idx]
        input_indices.append(next_idx)
    
    return result

def _build_trojan_payload(start_str, use_mutation):
    template = dict(random.choice(LEGIT_TEMPLATES))
    field, prefix = _extract_field_and_prefix(start_str)
    base_value = template.get(field, "")
    value = _merge_prefix(prefix, base_value)
    if use_mutation:
        mutation = np.random.choice(MUTATION_PAYLOADS)
        value = _inject_payload(value, mutation)
    template[field] = value
    return json.dumps(template, separators=(',', ':'), ensure_ascii=False)

def generate_valid_payload(start_str, temperature, length, use_mutation=True, max_attempts=5):
    if temperature >= 2.0:
        return generate_payload(start_str, temperature, length)
    return _build_trojan_payload(start_str, use_mutation)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.get_json()
        print(f"Получены данные: {data}")  # отладка
        if not data:
            return jsonify({'error': 'Некорректный JSON'}), 400
        
        start_str_input = data.get('start_str')
        temperature = float(data.get('temperature', 1.2))
        length = int(data.get('length', 80))
        count_raw = data.get('count', 1)
        try:
            count = int(count_raw)
        except (TypeError, ValueError):
            return jsonify({'error': 'count должен быть целым числом'}), 400
        if count < 1 or count > 500:
            return jsonify({'error': 'count должен быть в диапазоне 1..500'}), 400

        base_start = _normalize_start_str(start_str_input)
        payloads = []
        records = []
        timestamp = datetime.utcnow().isoformat() + "Z"
        for i in range(count):
            start_str = base_start
            use_mutation = np.random.rand() < 0.7
            if temperature >= 2.0 and use_mutation:
                start_str = _append_mutation(start_str, np.random.choice(MUTATION_PAYLOADS))
            payload = generate_valid_payload(start_str, temperature, length, use_mutation=use_mutation)
            payloads.append(payload)
            records.append({
                "timestamp": timestamp,
                "index": i,
                "seed": start_str_input,
                "start_str": start_str,
                "temperature": temperature,
                "length": length,
                "payload": payload
            })

        _append_jsonl(records, OUTPUT_JSONL)

        print(f"Сгенерировано payloads: {len(payloads)}")  # отладка
        
        return jsonify({'payloads': payloads, 'payload': payloads[0]})
    except Exception as e:
        print(f"Ошибка: {e}")
        return jsonify({'payload': f'Ошибка: {str(e)}'}), 500

if __name__ == '__main__':
    print(f"Рабочая папка: {os.getcwd()}")
    app.run(port=5000, debug=True)
