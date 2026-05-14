# 🚀 Fintech Payment Integration Service

> Production-ready asynchronous microservice for processing international payments with Stripe, built with FastAPI, PostgreSQL, Redis, and RabbitMQ.

A scalable fintech payment backend implementing **Repository** and **Service Layer** patterns with full SOLID compliance. Designed for high-throughput payment processing with built-in security, caching, and background job support.

---

## 🛠 Tech Stack

| Category | Technology |
|----------|------------|
| **Language** | Python 3.14 |
| **Framework** | FastAPI (Async) |
| **Database** | PostgreSQL 15 + SQLAlchemy 2.0 (Async) |
| **ORM** | SQLAlchemy 2.0 + Alembic |
| **Cache** | Redis 7 |
| **Message Queue** | RabbitMQ + aio-pika |
| **Authentication** | JWT (OAuth2) |
| **Payments** | Stripe API |
| **Testing** | Pytest + pytest-asyncio |
| **Container** | Docker + Docker Compose |
| **CI/CD** | GitHub Actions |

---

## 🏗 Architecture & Patterns

### Design Principles
- **SOLID** — Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion
- **DRY** — Don't Repeat Yourself
- **KISS** — Keep It Simple, Stupid

### Architectural Patterns
- **Repository Pattern** — Data access abstraction layer (`app/repositories/`)
- **Service Layer** — Business logic isolation (`app/services/`)
- **Abstract Factory** — Payment provider implementation (`app/payment_providers/`)

### Security Features
- 🔐 **JWT Authentication** — OAuth2 password bearer flow
- 🛡 **Webhook Signature Verification** — Stripe webhook authenticity validation
- 🔒 **Password Hashing** — Bcrypt with salt
- ✅ **Input Validation** — Pydantic models with strict type checking

### Key Features
- Asynchronous payment processing with RabbitMQ background jobs
- Redis caching for performance optimization
- Custom exception handling for financial transactions
- Database migrations with Alembic
- Comprehensive unit test coverage (52 tests)

---

## ⚙️ Fast Production Launch

### Quick Start (Docker Compose)

```bash
# 1. Clone the repository
git clone https://github.com/your-repo/fintech-payment-service.git
cd fintech-payment-service

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys (Stripe, JWT secret, etc.)

# 3. Launch all services
docker-compose up -d
```

### Services Exposed

| Service | URL | Description |
|---------|-----|-------------|
| **API** | http://localhost:8000 | FastAPI application |
| **Swagger UI** | http://localhost:8000/docs | Interactive API documentation |
| **ReDoc** | http://localhost:8000/redoc | Alternative API docs |
| **PostgreSQL** | localhost:5432 | Database (user: fintech, pass: fintech) |
| **Redis** | localhost:6379 | Cache |
| **RabbitMQ** | localhost:5672 | Message queue |
| **RabbitMQ Admin** | http://localhost:15672 | Management UI |
| **PGAdmin** | http://localhost:5050 | Database GUI |

### Manual Setup (Without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🧪 Testing

```bash
# Run all tests with coverage report
python -m pytest tests/ --cov=app --cov-report=term-missing

# Run tests in verbose mode
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_payment_service.py -v
```

### Test Results
```
============================= test session starts =============================
collected 52 items

tests/test_auth_service.py ..............                                [ 26%]
tests/test_core.py ..........                                            [ 46%]
tests/test_payment_providers.py ...............                          [ 75%]
tests/test_payment_service.py .............                              [100%]

============================== 52 passed in 7.20s ==============================
```

✅ **All 52 test cases passing** — 100% Green Coverage

---

## 📈 CI/CD

Automated GitHub Actions pipeline includes:

- ✅ **Linting** — Code style verification with Ruff
- ✅ **Unit Tests** — Automated test execution
- ✅ **Coverage Reports** — Code coverage analysis
- ✅ **Docker Build** — Multi-stage build for production
- ✅ **Security Scan** — Trivy vulnerability scanning

```yaml
# .github/workflows/ci.yml
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
```

---

## 📁 Project Structure

```
fintech-payment-service/
├── app/
│   ├── api/                    # REST API endpoints
│   │   ├── auth.py            # Authentication routes
│   │   ├── accounts.py        # Account management
│   │   └── payments.py        # Payment processing
│   ├── models/                # SQLAlchemy database models
│   ├── repositories/          # Data access layer
│   ├── services/              # Business logic layer
│   ├── payment_providers/     # Stripe integration
│   ├── config.py              # Application configuration
│   ├── database.py            # Database connection
│   ├── exceptions.py          # Custom exceptions
│   ├── security.py            # JWT authentication
│   ├── cache.py               # Redis caching
│   └── queue.py               # RabbitMQ integration
├── tests/                     # Test suite
├── alembic/                   # Database migrations
├── docker-compose.yml         # Docker orchestration
├── Dockerfile                 # Multi-stage build
├── requirements.txt           # Python dependencies
└── pyproject.toml            # Project configuration
```

---

## 🔌 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login (JWT token) |
| GET | `/api/v1/auth/me` | Get current user |

### Payments
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/payments` | Create payment |
| POST | `/api/v1/payments/{id}/capture` | Capture authorized payment |
| GET | `/api/v1/payments/{id}` | Get payment details |
| GET | `/api/v1/payments/account/{id}` | Get account payments |
| POST | `/api/v1/payments/webhook` | Stripe webhook handler |

### Accounts
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/accounts` | List user accounts |
| GET | `/api/v1/accounts/{id}` | Get account details |
| GET | `/api/v1/accounts/{id}/balance` | Get account balance |

---

## 📝 Configuration

Create `.env` file:

```env
# Database
DATABASE_URL=postgresql+asyncpg://fintech:fintech@db:5432/fintech

# Redis
REDIS_URL=redis://redis:6379/0

# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/

# JWT Authentication
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Stripe (Optional)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

---

## 📄 License

MIT License — feel free to use for your projects.

---

<div align="center">

**Built with ❤️ for fintech applications**

![Python](https://img.shields.io/badge/Python-3.14+-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=flat&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=flat&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)

</div>
