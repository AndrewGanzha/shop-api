# Shop API

FastAPI сервис интернет-магазина.

## Docker

Запуск приложения вместе с PostgreSQL:

```bash
docker compose up --build
```

API будет доступно на `http://localhost:8000`.

Примечание: сейчас приложение использует SQLite, контейнер PostgreSQL подготовлен для будущей миграции на него.
