# CivicPulse — System Architecture Document

## 1. System Overview

CivicPulse is a municipal technology platform connecting citizens with city administrators for transparent, location-verified civic problem resolution. The initial demonstration target city is **Vijayawada, India**, powered by an extensible multi-city database model.

---

## 2. Status: Implemented vs. Planned

To maintain clear architectural transparency, the current status is demarcated below:

### Implemented Foundation & Domain Models (v0.2.1)

| Layer | Implemented Components | Description |
| :--- | :--- | :--- |
| **Repository Structure** | Monorepo layout (`frontend/`, `backend/`, `docs/`) | Isolated dependencies, root `.gitignore`, environment templates with clear placeholders (`USER:PASSWORD`). |
| **Frontend Foundation** | React 19, JavaScript (ESM + JSX), Vite 8, Tailwind CSS v3, shadcn/ui primitives | Pure JavaScript/JSX architecture, path aliases (`@/*`), municipal deep green theme tokens, light/dark mode system. |
| **Frontend State & Data** | TanStack Query v5 & React Router v7 | Centralized query client with query cache and modern declarative routing structure. |
| **Backend Framework** | FastAPI + Python 3.11 + Uvicorn | App factory pattern with lifespan management, structured logging, thin route handlers. |
| **API Contracts** | Pydantic v2 schemas | `HealthResponse` and `DatabaseHealth` models with strict boundary validation. |
| **API Endpoints** | `GET /` and `GET /api/v1/health` | Operational health indicators, environment detection, and non-blocking database diagnostics. |
| **Security & CORS** | Whitelisted origin middleware & Zero Credential Guessing | Environment-driven `CORS_ORIGINS`. Never enumerates or guesses credentials; reports raw connection status. |
| **Domain Models** | SQLAlchemy 2.x Models (`app/models/`) | `City`, `Department`, `User`, `Complaint`, `ComplaintImage`, `ComplaintUpdate`, `Upvote`. |
| **Model Enums** | Native Python & PostgreSQL Enums | `UserRole` (`CITIZEN`, `ADMIN`), `ComplaintCategory` (10 civic categories), `ComplaintSeverity` (`LOW`, `MEDIUM`, `HIGH`), `ComplaintStatus` (6 lifecycle stages). |
| **Geographic Storage** | Temporary Numeric Coordinates | **Current:** PostgreSQL `Numeric(9, 6)` `latitude` and `longitude` with check constraints (`[-90, 90]` and `[-180, 180]`).<br>**Future:** Canonical PostGIS `geometry(Point, 4326)`. *(PostGIS is not currently installed or operational).* |
| **Database Migration** | Alembic Revision `21e2c13b255e` | Reproducible offline SQL generation and online execution creating all 7 tables, check constraints, foreign keys, unique indexes, and enums. |
| **Testing** | Pytest Test Suite (`tests/`) | 12 unit and smoke tests validating API endpoints, email uniqueness, role enums, complaint enums, progress percentage constraints, upvote unique constraints, user deletion restriction, required update actor, and cascade delete behavior. |

### Planned Features (Subsequent Phases)

| Phase / Module | Planned Capabilities |
| :--- | :--- |
| **Authentication & IAM** | Passwordless Email OTP authentication, salted OTP hashing, rate-limiting, JWT tokens, citizen vs. administrative role separation, CLI admin provisioning. |
| **Geospatial & PostGIS Migration** | PostGIS installation/configuration, migration of `(latitude, longitude)` to `geometry(Point, 4326)`, spatial indexing (`GIST`), EXIF coordinate verification, city polygon boundary containment checks. |
| **Priority Scoring Engine** | Decoupled scoring strategy in a dedicated service:<br>$$\text{Priority Score} = \text{Upvotes} + \text{Severity Weight}$$<br>($\text{LOW} = 10, \text{MEDIUM} = 25, \text{HIGH} = 50$). |
| **Complaint Lifecycle Service** | State machine transition enforcement (`SUBMITTED` $\to$ `UNDER_REVIEW` $\to$ `ASSIGNED` $\to$ `IN_PROGRESS` $\to$ `RESOLVED` / `REJECTED`) with immutable audit trails. |
| **Evidence Pipeline** | Client validation + Cloudinary signed upload proxy (max 3 images, JPEG/PNG/WebP, $\le 5\text{MB}$). |
| **Citizen Experience** | 4-step guided wizard (What, Where, Evidence, Review), anonymized public complaint feed, upvoting. |
| **Admin Operations Cockpit** | High-density priority triage table, city map view, department assignment, status remarks modal. |
| **Real-Time Communication** | FastAPI WebSockets connection manager broadcasting complaint update events without full-page reloads. |

---

## 3. Database Domain Entity Specification

```text
City
 ├── id (UUID, PK)
 ├── name (String, indexed)
 ├── state, country (String)
 ├── is_active (Boolean)
 └── Unique: (name, state, country)

Department
 ├── id (UUID, PK)
 ├── city_id (UUID, FK -> City.id, CASCADE)
 ├── name (String), description (Text)
 ├── is_active (Boolean)
 └── Unique: (city_id, name)

User
 ├── id (UUID, PK)
 ├── city_id (UUID, FK -> City.id, SET NULL)
 ├── email (String, unique, indexed, normalized)
 ├── full_name (String)
 ├── role (Enum: CITIZEN, ADMIN)
 └── is_active, is_verified (Boolean)

Complaint
 ├── id (UUID, PK)
 ├── city_id (UUID, FK -> City.id, RESTRICT)
 ├── user_id (UUID, FK -> User.id, RESTRICT)
 ├── department_id (UUID, FK -> Department.id, SET NULL)
 ├── title (String), description (Text)
 ├── category (Enum: ROADS, STREETLIGHTS, GARBAGE, DRAINAGE, WATER, SEWERAGE, TRAFFIC, PUBLIC_SAFETY, PARKS, OTHER)
 ├── severity (Enum: LOW, MEDIUM, HIGH)
 ├── status (Enum: SUBMITTED, UNDER_REVIEW, ASSIGNED, IN_PROGRESS, RESOLVED, REJECTED)
 ├── latitude, longitude (Numeric 9,6 - Temporary representation)
 └── Check: latitude [-90, 90], longitude [-180, 180]

ComplaintImage
 ├── id (UUID, PK)
 ├── complaint_id (UUID, FK -> Complaint.id, CASCADE)
 ├── image_url (String), public_id (String)
 └── latitude, longitude (Numeric 9,6 - EXIF GPS metadata)

ComplaintUpdate (Append-Only Audit History)
 ├── id (UUID, PK)
 ├── complaint_id (UUID, FK -> Complaint.id, CASCADE)
 ├── updated_by_user_id (UUID, FK -> User.id, RESTRICT, NOT NULL)
 ├── old_status, new_status (Enum: ComplaintStatus)
 ├── remark (Text), progress_percentage (Integer)
 └── Check: progress_percentage [0, 100]

Upvote
 ├── id (UUID, PK)
 ├── complaint_id (UUID, FK -> Complaint.id, CASCADE)
 ├── user_id (UUID, FK -> User.id, CASCADE)
 └── Unique: (complaint_id, user_id)
```

---

## 4. Architectural Principles

1. **Separation of Concerns:** Route handlers remain thin. Business logic resides in domain services; data access is encapsulated in models and repositories.
2. **JavaScript Frontend Standard:** Frontend strictly utilizes React with modern JavaScript/JSX (`.js`, `.jsx`) without TypeScript compilation overhead.
3. **Strict Credential Hygiene:** Never guess passwords, enumerate credentials, or store real secrets in Git. Databases and APIs authenticate strictly through environment-provided configurations.
4. **Civic Record Preservation:** Normal account removal deactivates users via `is_active=False`. Physical deletion of users is restricted (`ondelete="RESTRICT"`) when civic complaint records reference them, ensuring municipal history is never lost or orphaned.
5. **Append-Only Audit Trails:** `ComplaintUpdate` records are strictly append-only at the application/service layer. Lifecycle services may CREATE history records upon valid status changes, but must NEVER update or delete existing history entries. Every update requires an accountable user actor (`updated_by_user_id` is required).
6. **Geographic Roadmap:** Numeric coordinates are a temporary baseline. Models will be migrated to PostGIS `geometry(Point, 4326)` when PostGIS infrastructure is provisioned.
7. **Decoupled Scoring:** Priority calculations live in an isolated service layer rather than hardcoded DB columns or SQL triggers.