# Backend (Python / FastAPI)

Ядро системи, автентифікація користувачів та управління локаціями для проекту **Smart School Environment**.

## Технологічний стек
- **Мова**: Python 3.11+
- **Фреймворк**: FastAPI
- **ORM**: SQLAlchemy 2.0
- **Валідація**: Pydantic v2
- **Автентифікація**: JWT (JSON Web Tokens) + Bcrypt
- **База даних**: SQLite (за замовчуванням для локальної розробки) або PostgreSQL (для Docker)

---

## Швидкий запуск локально

1. Створити та активувати віртуальне середовище:
   ```bash
   python -m venv .venv
   # Windows PowerShell:
   .venv\Scripts\Activate.ps1
   # Linux/macOS:
   source .venv/bin/activate
   ```

2. Встановити залежності:
   ```bash
   pip install -r requirements.txt
   ```

3. Створити `.env` файл (можна скопіювати з прикладу):
   ```bash
   cp .env.example .env
   ```

4. Запустити сервер розробки:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

Сервер буде доступний за адресою: `http://localhost:8000`
Автоматична Swagger документація: `http://localhost:8000/docs`

---

## Запуск через Docker Compose

```bash
docker compose up --build
```

---

## Основні API ендпоінти

### Автентифікація (`/api/v1/auth`)
- `POST /api/v1/auth/register` — реєстрація нового користувача
- `POST /api/v1/auth/login` — вхід та отримання JWT токена
- `GET /api/v1/auth/me` — інформація про поточного авторизованого користувача

### Локації / Аудиторії (`/api/v1/locations`)
- `GET /api/v1/locations/` — отримати список усіх локацій
- `POST /api/v1/locations/` — створити нову локацію (потрібен токен)
- `GET /api/v1/locations/{id}` — отримати локацію за ID
- `PUT /api/v1/locations/{id}` — оновити дані локації (потрібен токен)
- `DELETE /api/v1/locations/{id}` — видалити локацію (потрібен токен)
