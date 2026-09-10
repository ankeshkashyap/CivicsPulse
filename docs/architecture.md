# CivicPulse — System Architecture Document

## 1. System Overview

CivicPulse is a municipal technology platform connecting citizens with city administrators for transparent, location-verified civic problem resolution. The initial demonstration target city is **Vijayawada, India**, designed with a multi-city data model.

---

## 2. Status: Implemented vs. Planned

To maintain clear architectural transparency, the current foundation status is demarcated below:

### Implemented Foundation (v0.1.0)

| Layer | Implemented Components | Description |
| :--- | :--- | :--- |
| **Repository Structure** | Monorepo layout (`frontend/`, `backend/`, `docs/`) | Isolated dependencies, root `.gitignore`, environment templates. |
| **Frontend Foundation** | React 19, TypeScript, Vite 8, Tailwind CSS v3, shadcn/ui primitives | Strict typing, path aliases (`@/*`), responsive layout, municipal deep green theme, light/dark token system. |
| **Frontend State & Data** | TanStack Query v5 & React Router v7 | Centralized query client with automated polling (`GET /api/v1/health`), cache management. |
| **Backend Framework** | FastAPI + Python 3.11 + Uvicorn | App factory pattern with lifespan management, structured logging, thin route handlers. |
| **API Contracts** | Pydantic v2 schemas | `HealthResponse` and `DatabaseHealth` models with strict validation. |
| **API Endpoints** | `GET /` and `GET /api/v1/health` | Operational health indicators, environment detection, and non-blocking database diagnostics. |
| **Error Handling** | Standardized JSON Exception Handlers | Unified response schema for `HTTPException` (4xx), `RequestValidationError` (422), and generic runtime errors (500). |
| **Security & CORS** | Whitelisted origin middleware | Environment-driven `CORS_ORIGINS` with strict headers and HTTP methods. |
| **Database Setup** | SQLAlchemy 2.x + Alembic + GeoAlchemy2 | Synchronous/asynchronous connection config, declarative base, timestamp mixins, migration runner with PostGIS table exclusions. |
| **Testing** | Pytest + Starlette TestClient + TypeScript compiler | Smoke tests for root, health, 404 handlers, and full production build verification. |

### Planned Features (Subsequent Phases)

| Phase / Module | Planned Capabilities |
| :--- | :--- |
| **Authentication & IAM** | Passwordless Email OTP authentication, salted OTP hashing, rate-limiting, JWT tokens, citizen vs. administrative role separation, CLI admin provisioning. |
| **Multi-City Core Models** | `City`, `Department`, `User`, `Complaint`, `ComplaintImage`, `ComplaintUpdate`, `Upvote`. |
| **Geospatial & PostGIS** | Canonical PostGIS `geometry(Point, 4326)` columns, spatial indexing, EXIF coordinate verification, city polygon containment checks. |
| **Priority Scoring Engine** | Decoupled scoring strategy: $\text{Priority} = \text{Upvotes} + \text{Severity Weight}$. |
| **Complaint Lifecycle Service** | State machine enforcement (`SUBMITTED` $\to$ `UNDER_REVIEW` $\to$ `ASSIGNED` $\to$ `IN_PROGRESS` $\to$ `RESOLVED` / `REJECTED`) with immutable audit trails. |
| **Evidence Pipeline** | Client validation + Cloudinary signed upload proxy (max 3 images, JPEG/PNG/WebP, $\le 5\text{MB}$). |
| **Citizen Experience** | 4-step guided wizard (What, Where, Evidence, Review), anonymized public complaint feed, upvoting. |
| **Admin Operations Cockpit** | High-density priority triage table, city map view, department assignment, status remarks modal. |
| **Real-Time Communication** | FastAPI WebSockets connection manager broadcasting complaint update events without full-page reloads. |

---

## 3. High-Level Architectural Principles

1. **Separation of Concerns:** Route handlers remain thin. Business logic resides in domain services; data access is encapsulated in repositories/models.
2. **Type Safety at All Boundaries:** Frontend and backend enforce type safety using TypeScript interfaces and Pydantic v2 schemas respectively.
3. **Defense in Depth:** Client-side authorization is never trusted; backend enforces role-based endpoint security and ownership verification.
4. **Canonical Spatial Architecture:** PostGIS is designated as the canonical spatial persistence mechanism rather than unindexed latitude/longitude columns.
5. **Operational Resilience:** Health checks verify subsystem availability without failing abruptly when downstream services are temporarily unreachable.