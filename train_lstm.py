import json
import torch
import torch.nn as nn
import pickle
import random
from torch.utils.data import DataLoader, TensorDataset


SEQ_LENGTH = 30
EMBEDDING_DIM = 64
HIDDEN_DIM = 128
BATCH_SIZE = 128          
EPOCHS = 80
TARGET_EXAMPLES = 1_000_000


print("Загрузка данных...")
with open("legitimate_requests.jsonl", "r", encoding="utf-8") as f:
    lines = [line.strip() for line in f if line.strip()]

texts = [json.loads(line) for line in lines]
json_strings = [json.dumps(obj, separators=(',', ':')) for obj in texts]

print(f"Загружено {len(json_strings)} JSON-запросов")

random.shuffle(json_strings)
json_strings = json_strings[:8000]   

print(f"Используем {len(json_strings)} JSON-объектов")

all_text = ''.join(json_strings)
chars = sorted(list(set(all_text)))
char_to_idx = {ch: i for i, ch in enumerate(chars)}
idx_to_char = {i: ch for i, ch in enumerate(chars)}
vocab_size = len(chars)

print(f"Размер алфавита: {vocab_size} символов")

print("Формирование обучающих пар...")
input_seqs = []
target_chars = []

for text in json_strings:
    for i in range(len(text) - SEQ_LENGTH):
        in_seq = text[i:i+SEQ_LENGTH]
        target = text[i + SEQ_LENGTH]
        input_seqs.append([char_to_idx[ch] for ch in in_seq])
        target_chars.append(char_to_idx[target])
        if len(input_seqs) >= TARGET_EXAMPLES:
            break
    if len(input_seqs) >= TARGET_EXAMPLES:
        break

X = torch.tensor(input_seqs, dtype=torch.long)
y = torch.tensor(target_chars, dtype=torch.long)
print(f"Сформировано {len(X):,} обучающих примеров")

class APIFuzzerNet(nn.Module):
    def __init__(self, vocab_size, embedding_dim, hidden_dim):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim)
        self.lstm = nn.LSTM(embedding_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, vocab_size)

    def forward(self, x, hidden=None):
        x = self.embedding(x)
        x, hidden = self.lstm(x, hidden)
        x = self.fc(x)
        return x, hidden

model = APIFuzzerNet(vocab_size, EMBEDDING_DIM, HIDDEN_DIM)
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

dataloader = DataLoader(TensorDataset(X, y), batch_size=BATCH_SIZE, shuffle=True)

print("\nНачинаем обучение...")
best_loss = float('inf')

for epoch in range(EPOCHS):
    total_loss = 0
    for batch_X, batch_y in dataloader:
        optimizer.zero_grad()
        output, _ = model(batch_X)
        loss = criterion(output[:, -1, :], batch_y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()

    avg_loss = total_loss / len(dataloader)
    
    if (epoch + 1) % 10 == 0:
        print(f"Эпоха {epoch+1}/{EPOCHS} | Loss: {avg_loss:.4f}")

    if avg_loss < best_loss:
        best_loss = avg_loss
        torch.save(model.state_dict(), "api_fuzzer_model_best.pth")

torch.save(model.state_dict(), "api_fuzzer_model_final.pth")
with open("char_to_idx.pkl", "wb") as f:
    pickle.dump(char_to_idx, f)
with open("idx_to_char.pkl", "wb") as f:
    pickle.dump(idx_to_char, f)

print("\n Обучение завершено!")
print(f"Лучший Loss: {best_loss:.4f}")