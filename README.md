## Данные об авторе
Войновская Виктория Эдуардовна
vojnovskay_ve_23
3 Курс / 6 семестр
Кибербезопасность
Курсовой проект


# API Fuzzer LSTM
Программный комплекс для интеллектуального тестирования безопасности (фаззинга) параметров Web API. Система использует рекуррентную нейронную сеть LSTM (PyTorch) для генерации валидных JSON-пакетов с мутированными вредоносными нагрузками (SQLi, SSTI, Path Traversal)

JSONL-файлы:
* `legitimate_requests.jsonl` — датасет легитимных запросов (каждая строка — отдельный JSON).
* `generated_payloads.jsonl` — журнал сгенерированных payload’ов (каждая строка — отдельный JSON).

## 🛠 Требования
* Python 3.9+
* pip

## Как запустить
1. Клонируйте репозиторий:
```
git clone https://github.com/voinovskayavictoria/my-course-project
cd repo
```
2. Установите зависимости:
```
pip install -r requirements.txt
```
3. Запустите проект:
```
python web_app.py
```

Откройте в браузере: http://localhost:5000

## Структура проекта
```
.
├─ web_app.py — веб-интерфейс (Flask) и генерация payload'ов
├─ index.html — фронтенд
├─ fuzz_generator.py — консольная генерация payload'ов
├─ train_lstm.py — обучение модели
├─ fuzz_sender.py — модуль отправки (полностью закомментирован)
├─ legitimate_requests.jsonl — датасет легитимных запросов
├─ generated_payloads.jsonl — лог сгенерированных payload'ов
├─ char_to_idx.pkl — словарь символ → индекс
├─ idx_to_char.pkl — словарь индекс → символ
├─ api_fuzzer_model.pth / api_fuzzer_model_best.pth / api_fuzzer_model_final.pth — веса модели
├─ requirements.txt — зависимости Python
├─ .gitignore — исключения для Git
└─ README.md — документация
```
