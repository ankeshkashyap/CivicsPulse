# CivicPulse — System Architecture Document

## 1. System Overview

CivicPulse is a municipal technology platform connecting citizens with city administrators for transparent, location-verified civic problem resolution. The initial demonstration target city is **Vijayawada, India**, powered by an extensible multi-city database model.

---

## 2. Status: Implemented vs. Planned

To maintain clear architectural transparency, the current status is demarcated below:

### Implemented Foundation, Domain Models & IAM (v0.3.0)

| Layer | Implemented Components | Description |
| :--- | :--- | :--- |
| **Repository Structure** | Monorepo layout (`frontend/`, `backend/`, `docs/`) | Isolated dependencies, root `.gitignore`, environment templates with clear placeholders (`USER:PASSWORD`). |
| **Frontend Foundation** | React 19, JavaScript (ESM + JSX), Vite 8, Tailwind CSS v3, shadcn/ui primitives | Pure JavaScript/JSX architecture, path aliases (`@/*`), municipal deep green theme tokens, light/dark mode system. |
| **Frontend State & Data** | TanStack Query v5 & React Router v7 | Centralized query client with query cache, AuthContext session state, and declarative routing. |
| **Frontend Auth Views** | `LoginForm`, `UserProfileCard`, `ProtectedRoute` | Minimal passwordless OTP login and verification cards, active session details, backend RBAC test trigger. |
| **Backend Framework** | FastAPI + Python 3.11 + Uvicorn | App factory pattern with lifespan management, structured logging, thin route handlers. |
| **API Contracts** | Pydantic v2 schemas | `HealthResponse`, `OTPRequest`, `OTPVerify`, `UserResponse`, `AuthResponse`, and `MessageResponse`. |
| **API Endpoints** | Health & Auth routes | `GET /api/v1/health`, `POST /api/v1/auth/request-otp`, `POST /api/v1/auth/verify-otp`, `GET /api/v1/auth/me`, `POST /api/v1/auth/logout`, and RBAC test routes. |
| **Authentication & IAM** | Passwordless Email-OTP & JWT | 6-digit secure random OTP, Argon2id hashing, 5-minute TTL, single-use consumption, max 5 attempts. HttpOnly cookies for browser session transport. |
| **Account Enumeration Defense** | Uniform response messages | `/request-otp` returns identical success response regardless of whether an account exists or is deactivated. |
| **Rate Limiting** | Email cooldown & IP sliding window | DB-backed cooldown (60s) per email; in-memory sliding window (10 requests/min) per client IP. |
| **Role Authorization** | Backend RBAC dependencies | `get_current_user`, `require_authenticated_user`, `require_citizen`, `require_admin`. Server-enforced security boundaries. |
| **Admin Provisioning** | Operator-only CLI tool | `python -m app.cli create-admin --email <email> --name <name>`. Public endpoints cannot assign `ADMIN` roles. |
| **Email Abstraction** | `EmailOTPProvider` interface | Pluggable `ConsoleEmailProvider` (dev/test) and `SMTPEmailProvider` (production). |
| **Domain Models** | SQLAlchemy 2.x Models (`app/models/`) | `City`, `Department`, `User`, `Complaint`, `ComplaintImage`, `ComplaintUpdate`, `Upvote`, `AuthOTPChallenge`. |
| **Model Enums** | Native Python & PostgreSQL Enums | `UserRole` (`CITIZEN`, `ADMIN`), `ComplaintCategory`, `ComplaintSeverity`, `ComplaintStatus`. |
| **Geographic Storage** | Temporary Numeric Coordinates | **Current:** PostgreSQL `Numeric(9, 6)` `latitude` and `longitude` with check constraints.<br>**Future:** Canonical PostGIS `geometry(Point, 4326)`. |
| **Database Migrations** | Alembic Revisions | `21e2c13b255e` (Domain models) and `3a7f8e91d012` (`auth_otp_challenges`). Verified via static SQL generation. |
| **Testing** | Comprehensive Pytest Test Suite | 35 automated tests (23 auth tests + 12 model/health tests) covering all 21 mandatory auth scenarios, rate limiting, and CLI provisioning. |

### Planned Features (Subsequent Phases)

| Phase / Module | Planned Capabilities |
| :--- | :--- |
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

AuthOTPChallenge (Dedicated Authentication Challenge Store)
 ├── id (UUID, PK)
 ├── email (String, indexed, normalized)
 ├── otp_hash (String, Argon2id hash)
 ├── expires_at (DateTime with timezone, indexed)
 ├── attempts (Integer, default 0)
 ├── max_attempts (Integer, default 5)
 ├── consumed_at (DateTime with timezone, nullable)
 ├── request_ip_hash (String, SHA-256 digest)
 ├── user_agent (String, truncated client UA)
 ├── last_attempt_at (DateTime with timezone, nullable)
 └── created_at (DateTime with timezone)
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

---

## 5. Authentication & IAM Architecture (Phase 04)

### 5.1 Passwordless Email-OTP Lifecycle
1. **Request:** `POST /api/v1/auth/request-otp` accepts an email, validates format via Pydantic, applies email cooldown (60s) and IP rate limiting (10 requests/min).
2. **Account Enumeration Defense:** Always returns `"If the email is eligible, an OTP has been sent."` regardless of whether the email exists, belongs to an admin, or belongs to a deactivated user.
3. **Challenge Generation:** Issues a 6-digit cryptographically random code (`secrets.randbelow`), hashes it with Argon2id, invalidates any existing unconsumed challenges for that email, and dispatches the code via `EmailOTPProvider`.
4. **Verification:** `POST /api/v1/auth/verify-otp` locates the active challenge, verifies the hash with constant-time protection, tracks failed attempts (locked at 5 attempts), and marks the challenge consumed upon success.
5. **Citizen Provisioning:** If the verified email does not exist, a new user is created with `role=CITIZEN`, `is_active=True`, and `is_verified=True`. Client-provided roles are ignored; self-elevation to `ADMIN` is strictly impossible.

### 5.2 Session Transport & JWT Strategy
- **Session Transport:** Issued via secure `HttpOnly`, `SameSite=Lax` cookie (`civicpulse_access_token`). In production, `secure=True` is enforced.
- **API & Testing Fallback:** `Authorization: Bearer <token>` is also supported for automated tests and non-browser clients.
- **JWT Claims:** Minimal payload containing `sub` (user UUID), `role` (`CITIZEN` or `ADMIN`), `iat`, and `exp`. No sensitive PII or secrets are embedded.
- **Logout:** `POST /api/v1/auth/logout` explicitly deletes the session cookie.

### 5.3 Administrative Provisioning
Admin accounts cannot be self-registered through HTTP endpoints. Admin accounts are provisioned exclusively via the operator CLI tool:
```bash
python -m app.cli create-admin --email admin@civicpulse.org --name "Chief Administrator"
```
Provisioned admins authenticate via the standard passwordless email-OTP flow, ensuring no passwords exist in the system.

### 5.4 Backend Role Authorization
Route security is enforced server-side using FastAPI dependency injection:
- `get_current_user`: extracts token from cookie/header, validates signature and expiration, retrieves user, and enforces `is_active=True`.
- `require_authenticated_user`: enforces active authenticated session.
- `require_citizen`: restricts endpoint to `UserRole.CITIZEN`.
- `require_admin`: restricts endpoint to `UserRole.ADMIN` (returns HTTP 403 `Insufficient permissions` otherwise).