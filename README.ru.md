# 🚀 Fintech Payment Integration Service

> Готовый к продакшену асинхронный микросервис для обработки международных платежей через Stripe, построенный на FastAPI, PostgreSQL, Redis и RabbitMQ.

Масштабируемый бэкенд для финтех-приложений с реализацией паттернов **Repository** и **Service Layer** с полным соблюдением принципов SOLID. Разработан для высоконагруженной обработки платежей со встроенной безопасностью, кешированием и поддержкой фоновых задач.

---

## 🛠 Технологический стек

| Категория | Технология |
|-----------|------------|
| **Язык** | Python 3.14 |
| **Фреймворк** | FastAPI (Async) |
| **База данных** | PostgreSQL 15 + SQLAlchemy 2.0 (Async) |
| **ORM** | SQLAlchemy 2.0 + Alembic |
| **Кеш** | Redis 7 |
| **Очередь сообщений** | RabbitMQ + aio-pika |
| **Аутентификация** | JWT (OAuth2) |
| **Платежи** | Stripe API |
| **Тестирование** | Pytest + pytest-asyncio |
| **Контейнеризация** | Docker + Docker Compose |
| **CI/CD** | GitHub Actions |

---

## 🏗 Архитектура и паттерны

### Принципы проектирования
- **SOLID** — Принципы единственной ответственности, открытости/закрытости, подстановки Барбары Лисков, разделения интерфейсов, инверсии зависимостей
- **DRY** — Не повторяйся
- **KISS** — Будь проще

### Архитектурные паттерны
- **Паттерн Repository** — Слой абстракции доступа к данным (`app/repositories/`)
- **Паттерн Service Layer** — Изоляция бизнес-логики (`app/services/`)
- **Абстрактная фабрика** — Реализация платёжного провайдера (`app/payment_providers/`)

### Функции безопасности
- 🔐 **JWT аутентификация** — OAuth2 password bearer flow
- 🛡 **Верификация подписи вебхуков** — Проверка подлинности Stripe вебхуков
- 🔒 **Хеширование паролей** — Bcrypt с солью
- ✅ **Валидация ввода** — Pydantic модели со строгой типизацией

### Ключевые возможности
- Асинхронная обработка платежей с фоновыми задачами в RabbitMQ
- Кеширование в Redis для оптимизации производительности
- Кастомная обработка исключений для финансовых транзакций
- Миграции базы данных через Alembic
- Комплектное покрытие юнит-тестами (52 теста)

---

## ⚡ Быстрый запуск в продакшен

### Быстрый старт (Docker Compose)

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/your-repo/fintech-payment-service.git
cd fintech-payment-service

# 2. Настройте окружение
cp .env.example .env
# Отредактируйте .env с вашими API ключами (Stripe, JWT secret и т.д.)

# 3. Запустите все сервисы
docker-compose up -d
```

### Доступные сервисы

| Сервис | URL | Описание |
|--------|-----|----------|
| **API** | http://localhost:8000 | Приложение FastAPI |
| **Swagger UI** | http://localhost:8000/docs | Интерактивная документация API |
| **ReDoc** | http://localhost:8000/redoc | Альтернативная документация |
| **PostgreSQL** | localhost:5432 | База данных (пользователь: fintech, пароль: fintech) |
| **Redis** | localhost:6379 | Кеш |
| **RabbitMQ** | localhost:5672 | Очередь сообщений |
| **RabbitMQ Admin** | http://localhost:15672 | Управление очередями |
| **PGAdmin** | http://localhost:5050 | GUI для базы данных |

### Ручная установка (Без Docker)

```bash
# Установите зависимости
pip install -r requirements.txt

# Запустите миграции базы данных
alembic upgrade head

# Запустите сервер
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🧪 Тестирование

```bash
# Запустите все тесты с отчётом о покрытии
python -m pytest tests/ --cov=app --cov-report=term-missing

# Запустите тесты в подробном режиме
python -m pytest tests/ -v

# Запустите конкретный файл тестов
python -m pytest tests/test_payment_service.py -v
```

### Результаты тестирования
```
============================= test session starts =============================
collected 52 items

tests/test_auth_service.py ..............                                [ 26%]
tests/test_core.py ..........                                            [ 46%]
tests/test_payment_providers.py ...............                          [ 75%]
tests/test_payment_service.py .............                              [100%]

============================== 52 passed in 7.20s ==============================
```

✅ **Все 52 тест-кейса пройдены** — 100% Green Coverage

---

## 📈 CI/CD

Автоматический пайплайн GitHub Actions включает:

- ✅ **Линтинг** — Проверка стиля кода с Ruff
- ✅ **Юнит-тесты** — Автоматическое выполнение тестов
- ✅ **Отчёты о покрытии** — Анализ покрытия кода
- ✅ **Сборка Docker** — Многоэтапная сборка для продакшена
- ✅ **Сканирование безопасности** — Сканирование уязвимостей Trivy

```yaml
# .github/workflows/ci.yml
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
```

---

## 📁 Структура проекта

```
fintech-payment-service/
├── app/
│   ├── api/                    # REST API эндпоинты
│   │   ├── auth.py            # Маршруты аутентификации
│   │   ├── accounts.py        # Управление счетами
│   │   └── payments.py        # Обработка платежей
│   ├── models/                # Модели базы данных SQLAlchemy
│   ├── repositories/          # Слой доступа к данным
│   ├── services/              # Слой бизнес-логики
│   ├── payment_providers/     # Интеграция Stripe
│   ├── config.py              # Конфигурация приложения
│   ├── database.py            # Подключение к базе данных
│   ├── exceptions.py          # Кастомные исключения
│   ├── security.py            # JWT аутентификация
│   ├── cache.py               # Кеширование Redis
│   └── queue.py               # Интеграция RabbitMQ
├── tests/                     # Набор тестов
├── alembic/                   # Миграции базы данных
├── docker-compose.yml         # Оркестрация Docker
├── Dockerfile                 # Многоэтапная сборка
├── requirements.txt           # Зависимости Python
└── pyproject.toml            # Конфигурация проекта
```

---

## 🔌 API эндпоинты

### Аутентификация
| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| POST | `/api/v1/auth/register` | Регистрация нового пользователя |
| POST | `/api/v1/auth/login` | Вход (JWT токен) |
| GET | `/api/v1/auth/me` | Получить текущего пользователя |

### Платежи
| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| POST | `/api/v1/payments` | Создать платёж |
| POST | `/api/v1/payments/{id}/capture` | Подтвердить авторизованный платёж |
| GET | `/api/v1/payments/{id}` | Получить детали платежа |
| GET | `/api/v1/payments/account/{id}` | Получить платежи счёта |
| POST | `/api/v1/payments/webhook` | Обработчик Stripe вебхуков |

### Счета
| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| GET | `/api/v1/accounts` | Список счетов пользователя |
| GET | `/api/v1/accounts/{id}` | Получить детали счёта |
| GET | `/api/v1/accounts/{id}/balance` | Получить баланс счёта |

---

## 📝 Конфигурация

Создайте файл `.env`:

```env
# База данных
DATABASE_URL=postgresql+asyncpg://fintech:fintech@db:5432/fintech

# Redis
REDIS_URL=redis://redis:6379/0

# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/

# JWT аутентификация
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Stripe (Опционально)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

---

## 📄 Лицензия

MIT License — используйте свободно в своих проектах.

---

<div align="center">

**Создано с ❤️ для финтех-приложений**

![Python](https://img.shields.io/badge/Python-3.14+-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=flat&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=flat&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)

</div>
