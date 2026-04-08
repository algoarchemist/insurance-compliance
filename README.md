# Sugamai — Unified Health Insurance Management Platform

> Simplifying health insurance for every Indian citizen. 🏥

## Overview

**Sugamai** is a standards-compliant (NHCX/FHIR R4), elder-friendly, AI-powered health insurance management platform. It helps citizens manage government and private health policies, find empanelled hospitals, file and track claims, and more — all from one place.

## Architecture

| Layer | Technology | Port |
|-------|-----------|------|
| **Backend API** | Python 3.11 + FastAPI | 8000 |
| **Frontend Web** | Next.js 14 + Tailwind CSS | 3000 |
| **Frontend Mobile** | React Native + Expo | 8081 |
| **Database** | PostgreSQL 15 | 5432 |
| **Cache / Queue** | Redis 7 | 6379 |
| **File Storage** | MinIO (S3-compatible) | 9000 |
| **Task Queue** | Celery + Redis | — |
| **Reverse Proxy** | Nginx | 80 |

### Folder Structure

```
sugamai/
├── backend/
│   ├── app/
│   │   ├── core/          # Database, redis, security, dependencies, MinIO, exceptions
│   │   ├── models/        # SQLAlchemy models (8 tables)
│   │   ├── schemas/       # Pydantic request/response schemas
│   │   ├── routers/       # API endpoints (9 routers, ~60 endpoints)
│   │   ├── services/      # Business logic + external API integrations (11 services)
│   │   ├── tasks/         # Celery async tasks (NHCX polling, OCR, notifications)
│   │   └── utils/         # JWE, FHIR, ICD codes, pagination
│   ├── alembic/           # Database migrations
│   ├── tests/             # Pytest test suites
│   ├── main.py            # FastAPI entry point
│   ├── config.py          # Pydantic settings
│   └── seed.py            # Sample data population
├── frontend-web/
│   └── src/
│       ├── app/[locale]/  # Next.js pages with i18n routing
│       ├── lib/           # API client (Axios + JWT interceptors)
│       ├── stores/        # Zustand state management
│       └── messages/      # i18n translations (5 languages)
├── frontend-mobile/
│   ├── app/               # Expo Router screens
│   └── lib/               # i18n config
├── infra/
│   └── nginx.conf         # Reverse proxy config
└── docker-compose.yml     # Full-stack orchestration
```

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 20+ (for frontend dev)
- Python 3.11+ (for backend dev)

### 1. Clone and configure

```bash
cp .env.example .env
# Edit .env with your API keys (optional — sandbox mocks work by default)
```

### 2. Start with Docker Compose

```bash
docker-compose up -d
```

This starts PostgreSQL, Redis, MinIO, Backend, Celery, and Frontend.

### 3. Seed the database

```bash
cd backend
pip install -r requirements.txt
python seed.py
```

### 4. Access

- **Web App:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs
- **MinIO Console:** http://localhost:9001 (sugamai / sugamai123)

### 5. Development

```bash
# Backend
cd backend
uvicorn main:app --reload --port 8000

# Frontend Web
cd frontend-web
npm install && npm run dev

# Frontend Mobile
cd frontend-mobile
npm install && npx expo start
```

## Features

### 🔐 Authentication
- Aadhaar-based OTP login (SHA-256 hashed — no raw storage)
- JWT tokens (30m access / 7d refresh)
- Role-based access control (User, Elder, Caregiver, Admin)

### 🆔 Identity (ABHA)
- Create/link ABHA health ID via ABDM sandbox
- PHR consent management

### 📋 Policy Management
- PMJAY eligibility auto-check via NHA API
- Private/employer policy registration
- Coverage tracking

### 🏥 Hospital Finder
- Location-based search with geo-distance
- Per-service coverage grid (cashless/sub-limit/not covered)
- AI-generated coverage summaries
- Pre-admission checklists

### 📄 Claims
- **Pre-authorization** → NHCX submission → approval polling
- **Cashless claims** → hospital admission → discharge → final bill
- **Reimbursement** → bill upload → OCR → AI parsing → submission
- AI gap detection before submission
- Real-time status tracking with timeline
- Bank account management with penny drop verification

### 🤖 AI Features (Claude)
- OCR bill parsing (Tesseract + Claude vision)
- Eligibility scoring across 8+ government schemes
- Coverage grid summaries in 5 languages
- Rejection code explanation with remediation steps
- Conversational eligibility chatbot

### 🤝 Caregiver
- Elder invites family member (max 2)
- Read-only dashboard for caregiver
- OTP consent flow for write actions
- Full audit trail

### ♿ Accessibility
- Large text mode
- High contrast mode
- Voice navigation (Web Speech API)
- 5 languages (English, Tamil, Hindi, Bengali, Telugu)

## API Endpoints

| Module | Prefix | Endpoints |
|--------|--------|-----------|
| Auth | `/api/v1/auth` | Aadhaar OTP, refresh, logout |
| Identity | `/api/v1/identity` | ABHA create/link/profile |
| Policies | `/api/v1/policies` | CRUD, PMJAY check, eligibility |
| Hospitals | `/api/v1/hospitals` | List, detail, coverage, NHCX check |
| Claims | `/api/v1/claims` | Pre-auth, cashless, reimbursement, OCR, FHIR, gaps, submit |
| Caregiver | `/api/v1/caregiver` | Invite, accept, elders, consent actions |
| AI | `/api/v1/ai` | Chat, coverage summary, rejection, bills, checklists |
| Admin | `/api/v1/admin` | Users, claims, audit logs, hospitals |
| Bank | `/api/v1/bank-accounts` | Add, list, delete (penny drop) |

## Security

- **Aadhaar:** SHA-256 hashed, never stored raw
- **Bank accounts:** AES-256 CFB encrypted at rest
- **NHCX payloads:** JWE encrypted (RSA-OAEP + A256GCM)
- **JWT:** Short-lived access (30m) + refresh (7d) with blacklisting
- **Rate limiting:** slowapi integration
- **CORS:** Restricted to known origins

## Testing

```bash
cd backend
pytest tests/ -v
```

## External API Integration

All integrations have **sandbox mock fallbacks** for local development:

| Service | API | Sandbox URL |
|---------|-----|-------------|
| UIDAI (Aadhaar) | OTP auth + eKYC | stage1.uidai.gov.in |
| ABDM (ABHA) | Health ID | sandbox.abdm.gov.in |
| NHCX | Claims exchange | dev.hcxprotocol.io |
| NHA (PMJAY) | Eligibility | pmjay.gov.in |
| Google Maps | Hospital search | maps.googleapis.com |
| Anthropic | AI features | api.anthropic.com |
| Twilio | SMS/OTP | api.twilio.com |
| Razorpay | Bank verification | api.razorpay.com |

## License

MIT
