# CivicPulse

CivicPulse is a municipal civic-tech platform connecting citizens and city administrators for transparent, location-verified complaint reporting and lifecycle tracking. The initial pilot city is **Vijayawada, India**, powered by an extensible multi-city architecture.

---

## 1. Technology Stack

### Frontend
- **Framework:** React 19 + JavaScript (JSX)
- **Tooling & Bundler:** Vite 8
- **Styling & Components:** Tailwind CSS v3, shadcn/ui design tokens, Lucide Icons
- **Data Fetching & Routing:** TanStack Query v5, React Router v7

### Backend
- **Framework:** FastAPI (Python 3.11+)
- **Validation & Serialization:** Pydantic v2
- **ORM & Data Layer:** SQLAlchemy 2.x, Alembic
- **Asynchronous Engine:** Uvicorn, AnyIO

### Database & Storage
- **Primary Database:** PostgreSQL
- **Geographic Data:**
  - **Current:** PostgreSQL `Numeric(9, 6)` `latitude` and `longitude` coordinates with check constraints
  - **Planned:** Canonical PostGIS `geometry(Point, 4326)` spatial types *(PostGIS is not currently installed or operational locally)*
- **Evidence Storage:** Cloudinary (planned)
- **Real-Time Updates:** FastAPI WebSockets (planned)

---

## 2. Repository Structure

```
CivicPulse/
├── frontend/                 # React 19 + JavaScript + Vite SPA
│   ├── src/
│   │   ├── components/ui/    # shadcn/ui foundational elements (button.jsx, card.jsx, badge.jsx)
│   │   ├── lib/              # Utility helpers (utils.js)
│   │   ├── App.jsx           # Clean development shell
│   │   ├── main.jsx          # QueryClient & Router entry point
│   │   └── index.css         # Civic design tokens & dark mode styles
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── .env.example
│
├── backend/                  # FastAPI 0.115+ Application
│   ├── app/
│   │   ├── api/v1/           # Versioned API routes & endpoints (Health)
│   │   ├── core/             # Configuration (pydantic-settings) & logging
│   │   ├── db/               # Base DeclarativeBase, Mixins, Sessionmaker, Health checker
│   │   ├── models/           # SQLAlchemy 2.x domain models (City, Department, User, Complaint, etc.)
│   │   ├── schemas/          # Pydantic request/response validation schemas
│   │   ├── services/         # Domain business logic layer
│   │   └── main.py           # FastAPI entry point, CORS & exception handlers
│   ├── alembic/              # Database migration environment
│   │   └── versions/         # Alembic migration revisions (21e2c13b255e)
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

## 3. Database Domain Models

CivicPulse defines 7 core relational entities:

1. **`City`:** Multi-city municipal entities (`name`, `state`, `country`, `is_active`).
2. **`Department`:** City-scoped administrative departments (`city_id`, `name`, `description`).
3. **`User`:** Citizen and administrator accounts (`email`, `full_name`, `role: CITIZEN | ADMIN`, `city_id`).
4. **`Complaint`:** Civic issues with category, severity, lifecycle status, and geographic coordinates.
5. **`ComplaintImage`:** Evidence metadata for photo uploads (`image_url`, `public_id`, EXIF GPS).
6. **`ComplaintUpdate`:** Immutable audit log tracking administrative transitions and progress (0–100%).
7. **`Upvote`:** Citizen community voting with `(complaint_id, user_id)` uniqueness.

---

## 4. Local Development Setup

### Backend Setup
1. Create and activate a virtual environment:
   ```bash
   cd backend
   python -m venv venv
   .\venv\Scripts\Activate.ps1   # Windows
   source venv/bin/activate      # Linux/macOS
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure environment variables in `backend/.env`:
   ```env
   DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@localhost:5432/civicpulse_dev
   ```

### Frontend Setup
1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

---

## 5. Migrations & Database Execution

1. **Generate offline migration SQL:**
   ```bash
   cd backend
   alembic upgrade head --sql
   ```
2. **Apply migrations online (requires running database with credentials):**
   ```bash
   alembic upgrade head
   ```

---

## 6. Running Tests

### Backend Tests (API smoke tests & Model unit tests):
```bash
cd backend
.\venv\Scripts\python -m pytest tests/ -v
```

### Frontend Production Build:
```bash
cd frontend
npm run build
```

---

## 7. Current Project Status

- **Version:** `v0.2.0` (Domain Model Foundation)
- **Status:** Core PostgreSQL domain models, enums, constraints, relationships, Alembic migration (`21e2c13b255e`), and model unit tests are fully implemented and verified.
- **Next Phase:** Phase 04 — Authentication (Passwordless Email OTP, JWT issuance, rate-limiting, and role authorization).