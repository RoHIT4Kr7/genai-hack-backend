from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
import json
import base64
import requests as http_requests
import os

from jose import jwt

from config.settings import settings

from jose import jwt

from config.settings import settings
from models.db import get_db
from models.user import User
from utils.auth import get_current_user


router = APIRouter(prefix="/auth", tags=["auth"])


class GoogleAuthRequest(BaseModel):
    credential: str


class AuthUser(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    profile_picture_url: Optional[str] = None


class AuthResponse(BaseModel):
    token: str
    token_type: str = "bearer"
    user: AuthUser


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = {"sub": subject, "iat": int(datetime.utcnow().timestamp())}
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.jwt_expires_minutes)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def manual_google_token_verification(token: str, expected_client_ids: list) -> dict:
    """
    Completely custom Google ID token verification that bypasses Google's library entirely.
    This eliminates all CRLF/whitespace issues by manually validating the JWT.
    """
    print(f"[CUSTOM AUTH] Starting manual token verification")
    print(
        f"[CUSTOM AUTH] Expected client IDs: {[id[:20]+'...' for id in expected_client_ids]}"
    )

    try:
        # Step 1: Decode JWT header without verification to get kid
        unverified_header = pyjwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        alg = unverified_header.get("alg", "RS256")

        print(f"[CUSTOM AUTH] Token algorithm: {alg}, key ID: {kid}")

        if alg != "RS256":
            raise ValueError(f"Unsupported algorithm: {alg}")

        # Step 2: Get Google's public keys
        print(f"[CUSTOM AUTH] Fetching Google public keys...")
        certs_url = "https://www.googleapis.com/oauth2/v1/certs"
        response = http_requests.get(certs_url, timeout=30)
        response.raise_for_status()
        certs = response.json()

        if kid not in certs:
            raise ValueError(f"Key ID {kid} not found in Google certificates")

        # Step 3: Load the public key and verify signature
        print(f"[CUSTOM AUTH] Loading public key for kid: {kid}")
        public_key_pem = certs[kid].encode("utf-8")
        public_key = load_pem_public_key(public_key_pem)

        # Step 4: Decode and verify the token
        print(f"[CUSTOM AUTH] Verifying token signature...")
        payload = pyjwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            options={"verify_aud": False},  # We'll verify audience manually
        )

        print(f"[CUSTOM AUTH] Token signature verified successfully")

        # Step 5: Manual validation of claims
        current_time = int(datetime.utcnow().timestamp())

        # Check expiry
        exp = payload.get("exp", 0)
        if current_time >= exp:
            print(f"[CUSTOM AUTH] Token expired: {current_time} >= {exp}")
            raise ValueError("Token has expired")

        # Check not before (optional)
        nbf = payload.get("nbf")
        if nbf and current_time < nbf:
            print(f"[CUSTOM AUTH] Token not yet valid: {current_time} < {nbf}")
            raise ValueError("Token not yet valid")

        # Check issuer
        iss = payload.get("iss", "")
        valid_issuers = ["accounts.google.com", "https://accounts.google.com"]
        if iss not in valid_issuers:
            print(f"[CUSTOM AUTH] Invalid issuer: {iss}")
            raise ValueError(f"Invalid issuer: {iss}")

        # Check audience (manual, sanitized comparison)
        token_aud = payload.get("aud", "").strip()
        print(f"[CUSTOM AUTH] Token audience: '{token_aud}'")

        # Sanitize all expected client IDs
        sanitized_expected = [cid.strip() for cid in expected_client_ids if cid]
        print(
            f"[CUSTOM AUTH] Sanitized expected audiences: {[id[:20]+'...' for id in sanitized_expected]}"
        )

        audience_match = False
        for expected_id in sanitized_expected:
            if token_aud == expected_id:
                print(f"[CUSTOM AUTH] Audience match found: {expected_id[:20]}...")
                audience_match = True
                break

        if not audience_match:
            print(f"[CUSTOM AUTH] No audience match found")
            print(f"[CUSTOM AUTH] Token audience: '{token_aud}'")
            print(f"[CUSTOM AUTH] Expected one of: {sanitized_expected}")
            raise ValueError(f"Invalid audience: {token_aud}")

        # Check essential claims
        if not payload.get("email"):
            raise ValueError("Email not present in token")

        if not payload.get("email_verified", False):
            print(f"[CUSTOM AUTH] Warning: Email not verified")

        print(f"[CUSTOM AUTH] All validations passed for email: {payload.get('email')}")
        return payload

    except Exception as e:
        print(f"[CUSTOM AUTH] Manual verification failed: {str(e)}")
        raise e


@router.get("/ping")
def auth_ping():
    """Canary endpoint to prove which revision is serving traffic"""
    revision = os.getenv("K_REVISION", "unknown")
    return {
        "auth_impl": "manual_v1",
        "revision": revision,
        "code_path": "manual_google_token_verification",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/google", response_model=AuthResponse)
def google_sign_in(
    payload: GoogleAuthRequest, response: Response, db: Session = Depends(get_db)
):
    print(f"[AUTH START] Google sign-in attempt started")

    if not payload.credential:
        print(f"[AUTH ERROR] Missing credential token")
        raise HTTPException(status_code=400, detail="Missing credential token")

    try:
        if not settings.google_client_id:
            print(f"[AUTH ERROR] GOOGLE_CLIENT_ID is not configured")
            raise HTTPException(
                status_code=500,
                detail="GOOGLE_CLIENT_ID is not configured on the server",
            )

        # Clean the client ID and create list of candidates
        clean_client_id = settings.google_client_id.strip()
        candidate_client_ids = [clean_client_id]

        # Debug logging for client ID
        print(f"[AUTH DEBUG] Raw client ID length: {len(settings.google_client_id)}")
        print(
            f"[AUTH DEBUG] Clean client ID: '{clean_client_id[:20]}...{clean_client_id[-20:]}' (truncated)"
        )
        print(
            f"[AUTH DEBUG] Client ID repr (first 50 chars): {repr(clean_client_id[:50])}"
        )
        print(f"[AUTH DEBUG] Token length: {len(payload.credential)}")
        print(f"[AUTH DEBUG] Token preview: {payload.credential[:50]}...")

        print(f"[AUTH DEBUG] Starting CUSTOM token verification...")
        # Use our completely custom verification to eliminate Google library issues
        idinfo = manual_google_token_verification(
            payload.credential, candidate_client_ids
        )
        print(f"[AUTH SUCCESS] Custom token verification completed")

        # Extract user info
        email = idinfo.get("email")
        name = idinfo.get("name")
        picture = idinfo.get("picture")
        google_sub = idinfo.get("sub")

        if not email:
            print(f"[AUTH ERROR] Email not present in token")
            raise HTTPException(status_code=400, detail="Email not present in token")

        print(f"[AUTH DEBUG] User info extracted - email: {email}, name: {name}")

        # Upsert user
        print(f"[AUTH DEBUG] Looking up user by email: {email}")
        user = db.query(User).filter(User.email == email).first()
        if user:
            print(f"[AUTH DEBUG] Existing user found, updating profile")
            # Update profile info if changed
            user.full_name = name or user.full_name
            user.profile_picture_url = picture or user.profile_picture_url
            if google_sub:
                user.google_id = google_sub
        else:
            print(f"[AUTH DEBUG] Creating new user")
            user = User(
                email=email,
                full_name=name,
                google_id=google_sub,
                profile_picture_url=picture,
            )
            db.add(user)
        db.commit()
        db.refresh(user)
        print(f"[AUTH DEBUG] User upsert completed, user ID: {user.id}")

        # Create our session JWT
        print(f"[AUTH DEBUG] Creating session JWT for user ID: {user.id}")
        token = create_access_token(subject=str(user.id))
        print(f"[AUTH SUCCESS] Authentication completed successfully for {email}")

        # Add hard-to-miss headers to prove this revision is serving traffic
        response.headers["X-Revision"] = os.getenv("K_REVISION", "unknown")
        response.headers["X-Code-Path"] = "manual_v1_verification"
        response.headers["X-Auth-Implementation"] = "manual_google_token_verification"

        return AuthResponse(
            token=token,
            user=AuthUser(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                profile_picture_url=user.profile_picture_url,
            ),
        )

    except ValueError as e:
        # Invalid token
        print(f"[AUTH] Invalid Google token verification error: {e}")
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Auth error: {e}")


@router.get("/debug/config")
def debug_auth_config():
    """Debug endpoint to check authentication configuration and detect CRLF contamination."""
    client_id = settings.google_client_id
    has_crlf = "\r" in client_id or "\n" in client_id

    return {
        "google_client_id_configured": bool(client_id),
        "google_client_id_length": len(client_id) if client_id else 0,
        "google_client_id_preview": (
            client_id[:20] + "..." + client_id[-10:]
            if client_id and len(client_id) > 30
            else client_id
        ),
        "google_client_id_repr": repr(client_id[:50]) if client_id else "None",
        "has_crlf_contamination": has_crlf,
        "cors_origins": settings.cors_origins_list,
        "jwt_algorithm": settings.jwt_algorithm,
        "environment": (
            "production" if "run.app" in os.getenv("GAE_SERVICE", "") else "development"
        ),
    }


@router.get("/me", response_model=AuthUser)
def get_me(current_user: User = Depends(get_current_user)):
    return AuthUser(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        profile_picture_url=current_user.profile_picture_url,
    )
