# CivicPulse

CivicPulse is a municipal civic-tech platform connecting citizens and city administrators for transparent, location-verified complaint reporting and lifecycle tracking. The initial pilot city is **Vijayawada, India**, powered by an extensible multi-city architecture.

---

## 1. Technology Stack

### Frontend
- **Framework:** React 19 + TypeScript
- **Tooling & Bundler:** Vite 8
- **Styling & Components:** Tailwind CSS v3, shadcn/ui design tokens, Lucide Icons
- **Data Fetching & Routing:** TanStack Query v5, React Router v7

### Backend
- **Framework:** FastAPI (Python 3.11+)
- **Validation & Serialization:** Pydantic v2
- **ORM & Data Layer:** SQLAlchemy 2.x, GeoAlchemy2, Alembic
- **Asynchronous Engine:** Uvicorn, AnyIO

### Database & Storage
- **Primary Database:** PostgreSQL 18 with canonical PostGIS spatial extensions
- **Evidence Storage:** Cloudinary (planned)
- **Real-Time Updates:** FastAPI WebSockets (planned)

---

## 2. Repository Structure

```
CivicPulse/
├── frontend/                 # React 19 + TypeScript + Vite SPA
│   ├── src/
│   │   ├── components/ui/    # shadcn/ui foundational elements (Button, Card, Badge)
│   │   ├── lib/              # Utility helpers (cn, clsx)
│   │   ├── App.tsx           # Foundation health status dashboard
│   │   ├── main.tsx          # QueryClient & Router entry point
│   │   └── index.css         # Civic design tokens & dark mode styles
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── .env.example
│
├── backend/                  # FastAPI 0.115+ Application
│   ├── app/
│   │   ├── api/v1/           # Versioned API routes & endpoints (Health)
│   │   ├── core/             # Configuration (pydantic-settings) & logging
│   │   ├── db/               # Base DeclarativeBase, Sessionmaker, Health checker
│   │   ├── models/           # SQLAlchemy entity models (Multi-city ready)
│   │   ├── schemas/          # Pydantic request/response validation schemas
│   │   ├── services/         # Domain business logic layer
│   │   └── main.py           # FastAPI entry point, CORS & exception handlers
│   ├── alembic/              # Database migration environment
│   ├── tests/                # Pytest test suite & TestClient fixtures
│   ├── alembic.ini
│   ├── requirements.txt
│   └── .env.example
│
├── docs/                     # Architecture & design documentation
│   └── architecture.md
├── .gitignore
├── README.md
└── .env.example              # Root environment template
```

---

## 3. Local Development Prerequisites

- **Python:** 3.11+
- **Node.js:** v20+ (v24.11+ supported) & **npm:** 10+
- **PostgreSQL:** PostgreSQL 16+ with PostGIS installed
- **Git:** 2.40+

---

## 4. Backend Setup

1. **Navigate to `backend/` and create virtual environment:**
   ```bash
   cd backend
   python -m venv venv
   ```

2. **Activate the virtual environment:**
   - **Windows (PowerShell):** `.\venv\Scripts\Activate.ps1`
   - **macOS / Linux:** `source venv/bin/activate`

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```

---

## 5. Frontend Setup

1. **Navigate to `frontend/`:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```

---

## 6. Database Setup & PostGIS Status

CivicPulse uses **PostGIS** as its canonical spatial data standard.

1. **Create the PostgreSQL database:**
   ```sql
   CREATE DATABASE civicpulse_dev;
   \c civicpulse_dev;
   CREATE EXTENSION IF NOT EXISTS postgis;
   ```

2. **Update `DATABASE_URL` in `backend/.env`:**
   ```env
   DATABASE_URL=postgresql+psycopg2://username:password@localhost:5432/civicpulse_dev
   ```

3. **Apply migrations:**
   ```bash
   alembic upgrade head
   ```

> **Note on Local Environment:** If running locally without PostGIS extension binaries installed on PostgreSQL, point `DATABASE_URL` to a PostGIS-enabled database instance (e.g. Supabase, Neon, or Docker with `postgis/postgis`).

---

## 7. Running the Application

### Start the Backend Server:
```bash
cd backend
# Windows:
.\venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
# macOS/Linux:
python -m uvicorn app.main:app --reload --port 8000
```
- Interactive API Docs: `http://localhost:8000/docs`
- Health Endpoint: `http://localhost:8000/api/v1/health`

### Start the Frontend Dev Server:
```bash
cd frontend
npm run dev
```
- Web Application: `http://localhost:5173`

---

## 8. Verification & Smoke Tests

### Backend Test Suite:
```bash
cd backend
.\venv\Scripts\python -m pytest tests/ -v
```

### Frontend Type Check & Production Build:
```bash
cd frontend
npm run build
```

---

## 9. Current Project Status

- **Version:** `v0.1.0` (Foundation Stage)
- **Status:** Greenfield initialization complete. Core monorepo structure, FastAPI engine, React 19 client, Tailwind theme tokens, health monitoring, error handling, and test runners are verified and operational.
- **Next Phase:** Multi-city data models, PostGIS integration, and passwordless email OTP authentication.