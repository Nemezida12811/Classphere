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

4. Запустити сервер розробки (порт **3001** — його очікує frontend):
   ```bash
   python -m app            # або: uvicorn app.main:app --reload --port 3001
   ```

Сервер буде доступний за адресою: `http://localhost:3001`
Автоматична Swagger документація: `http://localhost:3001/docs`

> Якщо база `school_env.db` лишилась від старої версії — видаліть її: у таблицю `locations` додано колонку `admin_id`, а `create_all` існуючі таблиці не змінює.

---

## Запуск без фізичного пристрою (backend + frontend)

У `.env` має бути `SIMULATE_DEVICE=true` (є в `.env.example`). Тоді backend сам генерує телеметрію
3 кімнат (`school-day`, `comfortable`, `stuffy`) у тому ж форматі, що й прошивка (ISO-час, сирі 16-бітні
значення АЦП), і пропускає її через той самий конвеєр, що й MQTT — **MQTT-брокер не потрібен**.

```bash
# термінал 1
cd backend && python -m app
# термінал 2
cd frontend/client && npm install && npm run dev
```
1. Список id симульованих пристроїв: `GET http://localhost:3001/api/simulator/devices`
   (також друкується в консолі backend; id стабільні: `com-0a6085b9ed2396e6-fort`, …).
2. У frontend: зареєструйтесь → створіть локацію → «Add room» → вставте id пристрою.
3. Швидкість моделі: `SIM_INTERVAL_SECONDS` (період вимірювань) і `SIM_SPEED` (1 с реального часу = N с моделі).

Справжні пристрої через MQTT: задайте `MQTT_URL=mqtt://host:1883` (залежність `paho-mqtt`).

Рекомендації в `/api/comfort/{id}/recommendations` формуються правилами (без OpenAI).

---

## Запуск через Docker Compose

```bash
docker compose up --build
```
Backend буде на `http://localhost:3001` (симулятор увімкнено у `docker-compose.yml`).

---

## Основні API ендпоінти

### Для frontend (`/api/...`, відповіді `{"success": true, "data": ...}`, помилки `{"success": false, "error": "..."}`)
- `POST /api/auth/register`, `POST /api/auth/login` (JSON `{email, password}`), `POST /api/auth/logout`, `GET /api/auth/me`
- `GET|POST /api/locations`, `GET|PATCH|DELETE /api/locations/{id}`
- `POST /api/locations/{id}/users`, `DELETE /api/locations/{id}/users/{userId}`
- `POST /api/locations/{id}/devices`, `PATCH .../devices/{deviceId}/hide|show`, `DELETE .../devices/{deviceId}`
- `GET /api/comfort/{deviceId}`, `/api/comfort/{deviceId}/recommendations`, `/api/comfort/{deviceId}/sensors`
- `GET /api/simulator/devices`

### Класичний REST (`/api/v1`)

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
