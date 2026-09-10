import uuid
from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy import select

from app.core.config import settings
from app.models.auth_otp import AuthOTPChallenge
from app.models.enums import UserRole
from app.models.user import User
from app.services.auth_service import provision_admin_user, _ip_request_timestamps
from app.services.jwt_service import create_access_token


# --------------------------------------------------------------------------
# 1. Valid OTP succeeds
# --------------------------------------------------------------------------
def test_01_valid_otp_succeeds(auth_client, email_provider, db_session):
    email = "citizen1@example.com"
    req_res = auth_client.post("/api/v1/auth/request-otp", json={"email": email})
    assert req_res.status_code == 200
    assert req_res.json()["message"] == "If the email is eligible, an OTP has been sent."

    otp = email_provider.get_last_otp(email)
    assert otp is not None
    assert len(otp) == 6

    verify_res = auth_client.post("/api/v1/auth/verify-otp", json={"email": email, "otp": otp})
    assert verify_res.status_code == 200
    data = verify_res.json()
    assert data["message"] == "Authentication successful"
    assert data["user"]["email"] == email
    assert data["user"]["role"] == "CITIZEN"
    assert data["token"] is not None

    # Check HttpOnly cookie
    assert settings.AUTH_COOKIE_NAME in verify_res.cookies
    cookie = verify_res.cookies[settings.AUTH_COOKIE_NAME]
    assert cookie == data["token"]


# --------------------------------------------------------------------------
# 2. Invalid OTP fails
# --------------------------------------------------------------------------
def test_02_invalid_otp_fails(auth_client, email_provider, db_session):
    email = "citizen2@example.com"
    auth_client.post("/api/v1/auth/request-otp", json={"email": email})
    otp = email_provider.get_last_otp(email)

    wrong_otp = "000000" if otp != "000000" else "111111"
    verify_res = auth_client.post("/api/v1/auth/verify-otp", json={"email": email, "otp": wrong_otp})
    assert verify_res.status_code == 400
    assert "Invalid or expired OTP" in verify_res.json()["message"]

    # Verify attempt count incremented in DB
    challenge = db_session.scalars(
        select(AuthOTPChallenge).where(AuthOTPChallenge.email == email)
    ).first()
    assert challenge is not None
    assert challenge.attempts == 1
    assert challenge.consumed_at is None


# --------------------------------------------------------------------------
# 3. Expired OTP fails
# --------------------------------------------------------------------------
def test_03_expired_otp_fails(auth_client, email_provider, db_session):
    email = "citizen3@example.com"
    auth_client.post("/api/v1/auth/request-otp", json={"email": email})
    otp = email_provider.get_last_otp(email)

    # Force challenge to be expired in DB
    challenge = db_session.scalars(
        select(AuthOTPChallenge).where(AuthOTPChallenge.email == email)
    ).first()
    challenge.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db_session.commit()

    verify_res = auth_client.post("/api/v1/auth/verify-otp", json={"email": email, "otp": otp})
    assert verify_res.status_code == 400
    assert "Invalid or expired OTP" in verify_res.json()["message"]


# --------------------------------------------------------------------------
# 4. Consumed OTP cannot be reused
# --------------------------------------------------------------------------
def test_04_consumed_otp_cannot_be_reused(auth_client, email_provider, db_session):
    email = "citizen4@example.com"
    auth_client.post("/api/v1/auth/request-otp", json={"email": email})
    otp = email_provider.get_last_otp(email)

    # First verification succeeds
    res1 = auth_client.post("/api/v1/auth/verify-otp", json={"email": email, "otp": otp})
    assert res1.status_code == 200

    # Second verification fails
    res2 = auth_client.post("/api/v1/auth/verify-otp", json={"email": email, "otp": otp})
    assert res2.status_code == 400
    assert "Invalid or expired OTP" in res2.json()["message"]


# --------------------------------------------------------------------------
# 5. Too many failed attempts invalidates challenge
# --------------------------------------------------------------------------
def test_05_too_many_failed_attempts_locks_challenge(auth_client, email_provider, db_session):
    email = "citizen5@example.com"
    auth_client.post("/api/v1/auth/request-otp", json={"email": email})
    otp = email_provider.get_last_otp(email)
    wrong_otp = "000000" if otp != "000000" else "111111"

    # Make 4 failed attempts
    for _ in range(4):
        res = auth_client.post("/api/v1/auth/verify-otp", json={"email": email, "otp": wrong_otp})
        assert res.status_code == 400
        assert "Invalid or expired OTP" in res.json()["message"]

    # 5th failed attempt locks challenge
    res5 = auth_client.post("/api/v1/auth/verify-otp", json={"email": email, "otp": wrong_otp})
    assert res5.status_code == 400
    assert "Too many OTP attempts" in res5.json()["message"]

    # 6th attempt (even with valid OTP) is rejected because challenge is locked
    res6 = auth_client.post("/api/v1/auth/verify-otp", json={"email": email, "otp": otp})
    assert res6.status_code == 400
    assert "Too many OTP attempts" in res6.json()["message"]


# --------------------------------------------------------------------------
# 6. New OTP supersedes previous OTP
# --------------------------------------------------------------------------
def test_06_new_otp_supersedes_previous_otp(auth_client, email_provider, db_session):
    email = "citizen6@example.com"
    auth_client.post("/api/v1/auth/request-otp", json={"email": email})
    otp1 = email_provider.get_last_otp(email)

    # Fast-forward created_at of challenge 1 to bypass cooldown
    challenge1 = db_session.scalars(
        select(AuthOTPChallenge).where(AuthOTPChallenge.email == email)
    ).first()
    challenge1.created_at = datetime.now(timezone.utc) - timedelta(seconds=settings.OTP_COOLDOWN_SECONDS + 5)
    db_session.commit()

    # Request new OTP
    auth_client.post("/api/v1/auth/request-otp", json={"email": email})
    otp2 = email_provider.get_last_otp(email)

    # Attempting to use old OTP1 fails
    res_old = auth_client.post("/api/v1/auth/verify-otp", json={"email": email, "otp": otp1})
    assert res_old.status_code == 400

    # Using new OTP2 succeeds
    res_new = auth_client.post("/api/v1/auth/verify-otp", json={"email": email, "otp": otp2})
    assert res_new.status_code == 200


# --------------------------------------------------------------------------
# 7. OTP is never stored as plaintext
# --------------------------------------------------------------------------
def test_07_otp_never_stored_as_plaintext(auth_client, email_provider, db_session):
    email = "citizen7@example.com"
    auth_client.post("/api/v1/auth/request-otp", json={"email": email})
    otp = email_provider.get_last_otp(email)

    challenge = db_session.scalars(
        select(AuthOTPChallenge).where(AuthOTPChallenge.email == email)
    ).first()
    assert challenge is not None
    assert challenge.otp_hash != otp
    assert challenge.otp_hash.startswith("$argon2id$")
    assert otp not in challenge.otp_hash


# --------------------------------------------------------------------------
# 8. New valid citizen OTP creates a citizen
# --------------------------------------------------------------------------
def test_08_new_valid_citizen_otp_creates_citizen(auth_client, email_provider, db_session):
    email = "newcitizen@example.com"
    auth_client.post("/api/v1/auth/request-otp", json={"email": email})
    otp = email_provider.get_last_otp(email)

    res = auth_client.post("/api/v1/auth/verify-otp", json={"email": email, "otp": otp})
    assert res.status_code == 200

    user = db_session.scalars(select(User).where(User.email == email)).first()
    assert user is not None
    assert user.role == UserRole.CITIZEN
    assert user.is_active is True
    assert user.is_verified is True


# --------------------------------------------------------------------------
# 9. Existing citizen can authenticate
# --------------------------------------------------------------------------
def test_09_existing_citizen_can_authenticate(auth_client, email_provider, db_session):
    email = "existingcitizen@example.com"
    existing_user = User(
        email=email,
        full_name="Existing Citizen",
        role=UserRole.CITIZEN,
        is_active=True,
        is_verified=True,
    )
    db_session.add(existing_user)
    db_session.commit()
    user_id = existing_user.id

    auth_client.post("/api/v1/auth/request-otp", json={"email": email})
    otp = email_provider.get_last_otp(email)

    res = auth_client.post("/api/v1/auth/verify-otp", json={"email": email, "otp": otp})
    assert res.status_code == 200
    data = res.json()
    assert data["user"]["id"] == str(user_id)
    assert data["user"]["full_name"] == "Existing Citizen"


# --------------------------------------------------------------------------
# 10. Inactive user cannot authenticate
# --------------------------------------------------------------------------
def test_10_inactive_user_cannot_authenticate(auth_client, email_provider, db_session):
    email = "inactiveuser@example.com"
    user = User(
        email=email,
        full_name="Deactivated User",
        role=UserRole.CITIZEN,
        is_active=False,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()

    # Requesting OTP for inactive account still returns generic message (enumeration defense)
    req_res = auth_client.post("/api/v1/auth/request-otp", json={"email": email})
    assert req_res.status_code == 200
    assert req_res.json()["message"] == "If the email is eligible, an OTP has been sent."

    # No OTP is dispatched for inactive user
    assert email_provider.get_last_otp(email) is None

    # Even if an inactive user attempts to use a valid JWT, access is denied
    token = create_access_token(user_id=user.id, role="CITIZEN")
    me_res = auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 403
    assert "Inactive account" in me_res.json()["message"]


# --------------------------------------------------------------------------
# 11. User email normalization works
# --------------------------------------------------------------------------
def test_11_user_email_normalization_works(auth_client, email_provider, db_session):
    mixed_email = "  MiXeD.CaSe@Example.Com  "
    expected_email = "mixed.case@example.com"

    auth_client.post("/api/v1/auth/request-otp", json={"email": mixed_email})
    otp = email_provider.get_last_otp(expected_email)
    assert otp is not None

    # Verify using another casing variation
    verify_res = auth_client.post("/api/v1/auth/verify-otp", json={"email": "MIXED.CASE@EXAMPLE.COM", "otp": otp})
    assert verify_res.status_code == 200
    assert verify_res.json()["user"]["email"] == expected_email

    # Check user record in database
    user = db_session.scalars(select(User).where(User.email == expected_email)).first()
    assert user is not None
    assert user.email == expected_email


# --------------------------------------------------------------------------
# 12. Client cannot create an ADMIN account
# --------------------------------------------------------------------------
def test_12_client_cannot_create_admin_account(auth_client, email_provider, db_session):
    email = "attacker@example.com"
    auth_client.post("/api/v1/auth/request-otp", json={"email": email})
    otp = email_provider.get_last_otp(email)

    # Client attempts to pass role: ADMIN in body
    verify_res = auth_client.post(
        "/api/v1/auth/verify-otp",
        json={"email": email, "otp": otp, "role": "ADMIN"},
    )
    assert verify_res.status_code == 200
    data = verify_res.json()
    assert data["user"]["role"] == "CITIZEN"

    user = db_session.scalars(select(User).where(User.email == email)).first()
    assert user.role == UserRole.CITIZEN


# --------------------------------------------------------------------------
# 13. Valid JWT authenticates
# --------------------------------------------------------------------------
def test_13_valid_jwt_authenticates(auth_client, db_session):
    user = User(
        email="jwtuser@example.com",
        role=UserRole.CITIZEN,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()

    token = create_access_token(user_id=user.id, role="CITIZEN")

    # 1. Authenticate via Bearer header
    res_header = auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_header.status_code == 200
    assert res_header.json()["email"] == "jwtuser@example.com"

    # 2. Authenticate via HttpOnly cookie
    auth_client.cookies.set(settings.AUTH_COOKIE_NAME, token)
    res_cookie = auth_client.get("/api/v1/auth/me")
    assert res_cookie.status_code == 200
    assert res_cookie.json()["email"] == "jwtuser@example.com"
    auth_client.cookies.clear()


# --------------------------------------------------------------------------
# 14. Expired JWT fails
# --------------------------------------------------------------------------
def test_14_expired_jwt_fails(auth_client, db_session):
    user = User(
        email="expireduser@example.com",
        role=UserRole.CITIZEN,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()

    expired_token = create_access_token(
        user_id=user.id,
        role="CITIZEN",
        expires_delta=timedelta(seconds=-10),
    )

    res = auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert res.status_code == 401
    assert "expired" in res.json()["message"].lower()


# --------------------------------------------------------------------------
# 15. Invalid JWT fails
# --------------------------------------------------------------------------
def test_15_invalid_jwt_fails(auth_client):
    res = auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not.a.valid.jwt.signature"},
    )
    assert res.status_code == 401
    assert "invalid" in res.json()["message"].lower()


# --------------------------------------------------------------------------
# 16. Missing authentication fails
# --------------------------------------------------------------------------
def test_16_missing_authentication_fails(auth_client):
    auth_client.cookies.clear()
    res = auth_client.get("/api/v1/auth/me")
    assert res.status_code == 401
    assert "Authentication required" in res.json()["message"]


# --------------------------------------------------------------------------
# 17. GET /auth/me returns the authenticated user
# --------------------------------------------------------------------------
def test_17_get_auth_me_returns_authenticated_user(auth_client, db_session):
    user = User(
        email="profileuser@example.com",
        full_name="Vijayawada Citizen",
        role=UserRole.CITIZEN,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()

    token = create_access_token(user_id=user.id, role="CITIZEN")
    res = auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == str(user.id)
    assert data["email"] == "profileuser@example.com"
    assert data["full_name"] == "Vijayawada Citizen"
    assert data["role"] == "CITIZEN"
    assert data["is_verified"] is True
    # Verify no sensitive hash/secret fields are exposed
    assert "otp_hash" not in data
    assert "secret" not in data


# --------------------------------------------------------------------------
# 18. Citizen cannot satisfy admin authorization
# --------------------------------------------------------------------------
def test_18_citizen_cannot_satisfy_admin_authorization(auth_client, db_session):
    citizen = User(
        email="normalcitizen@example.com",
        role=UserRole.CITIZEN,
        is_active=True,
        is_verified=True,
    )
    db_session.add(citizen)
    db_session.commit()

    token = create_access_token(user_id=citizen.id, role="CITIZEN")

    # Access citizen route succeeds
    res_citizen = auth_client.get(
        "/api/v1/auth/test-citizen",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_citizen.status_code == 200

    # Access admin route fails with 403 Insufficient permissions
    res_admin = auth_client.get(
        "/api/v1/auth/test-admin",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_admin.status_code == 403
    assert "Insufficient permissions" in res_admin.json()["message"]


# --------------------------------------------------------------------------
# 19. Admin can satisfy admin authorization
# --------------------------------------------------------------------------
def test_19_admin_can_satisfy_admin_authorization(auth_client, db_session):
    admin = provision_admin_user(
        email="municipaladmin@civicpulse.org",
        db=db_session,
        full_name="Municipal Commissioner",
    )
    assert admin.role == UserRole.ADMIN

    token = create_access_token(user_id=admin.id, role="ADMIN")
    res_admin = auth_client.get(
        "/api/v1/auth/test-admin",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_admin.status_code == 200
    assert "municipaladmin@civicpulse.org" in res_admin.json()["message"]


# --------------------------------------------------------------------------
# 20. Logout clears/invalidates session
# --------------------------------------------------------------------------
def test_20_logout_clears_session(auth_client, email_provider):
    email = "logouttest@example.com"
    auth_client.post("/api/v1/auth/request-otp", json={"email": email})
    otp = email_provider.get_last_otp(email)
    verify_res = auth_client.post("/api/v1/auth/verify-otp", json={"email": email, "otp": otp})

    assert settings.AUTH_COOKIE_NAME in verify_res.cookies
    token = verify_res.cookies[settings.AUTH_COOKIE_NAME]
    auth_client.cookies.set(settings.AUTH_COOKIE_NAME, token)

    logout_res = auth_client.post("/api/v1/auth/logout")
    assert logout_res.status_code == 200
    assert logout_res.json()["message"] == "Successfully logged out"

    # Verify cookie clearance header was dispatched
    cookie_header = logout_res.headers.get("set-cookie", "")
    assert settings.AUTH_COOKIE_NAME in cookie_header


# --------------------------------------------------------------------------
# 21. OTP request responses do not reveal whether an account exists
# --------------------------------------------------------------------------
def test_21_enumeration_defense(auth_client, db_session):
    # Existing active citizen
    c1 = User(email="c1@example.com", role=UserRole.CITIZEN, is_active=True)
    # Existing deactivated citizen
    c2 = User(email="c2@example.com", role=UserRole.CITIZEN, is_active=False)
    # Existing admin
    admin = User(email="adm@example.com", role=UserRole.ADMIN, is_active=True)
    db_session.add_all([c1, c2, admin])
    db_session.commit()

    # Clear IP rate limiter
    _ip_request_timestamps.clear()

    res_existing = auth_client.post("/api/v1/auth/request-otp", json={"email": "c1@example.com"})
    res_inactive = auth_client.post("/api/v1/auth/request-otp", json={"email": "c2@example.com"})
    res_admin = auth_client.post("/api/v1/auth/request-otp", json={"email": "adm@example.com"})
    res_nonexistent = auth_client.post("/api/v1/auth/request-otp", json={"email": "nobody@example.com"})

    expected_body = {"message": "If the email is eligible, an OTP has been sent."}
    assert res_existing.status_code == 200 and res_existing.json() == expected_body
    assert res_inactive.status_code == 200 and res_inactive.json() == expected_body
    assert res_admin.status_code == 200 and res_admin.json() == expected_body
    assert res_nonexistent.status_code == 200 and res_nonexistent.json() == expected_body


# --------------------------------------------------------------------------
# 22. Rate limiting cooldown on rapid OTP requests
# --------------------------------------------------------------------------
def test_22_rate_limiting_cooldown(auth_client, db_session):
    email = "ratelimit@example.com"
    _ip_request_timestamps.clear()

    res1 = auth_client.post("/api/v1/auth/request-otp", json={"email": email})
    assert res1.status_code == 200

    # Rapid second request within cooldown triggers 429
    res2 = auth_client.post("/api/v1/auth/request-otp", json={"email": email})
    assert res2.status_code == 429
    assert "Too many OTP requests" in res2.json()["message"]


# --------------------------------------------------------------------------
# 23. CLI Admin Provisioning tool
# --------------------------------------------------------------------------
def test_23_cli_admin_provisioning(db_session, monkeypatch):
    from app.cli.__main__ import main

    # Run CLI command via sys.argv emulation
    test_args = ["python", "create-admin", "--email", "cli.admin@civicpulse.org", "--name", "CLI Administrator"]
    monkeypatch.setattr("sys.argv", test_args)
    monkeypatch.setattr("app.cli.__main__.SessionLocal", lambda: db_session)

    exit_code = main()
    assert exit_code == 0

    user = db_session.scalars(select(User).where(User.email == "cli.admin@civicpulse.org")).first()
    assert user is not None
    assert user.role == UserRole.ADMIN
    assert user.full_name == "CLI Administrator"
    assert user.is_active is True
    assert user.is_verified is True
