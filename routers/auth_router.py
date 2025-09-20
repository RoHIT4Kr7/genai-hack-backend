from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from google.oauth2 import id_token
from google.auth.transport import requests
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


@router.post("/google", response_model=AuthResponse)
def google_sign_in(payload: GoogleAuthRequest, db: Session = Depends(get_db)):
    if not payload.credential:
        raise HTTPException(status_code=400, detail="Missing credential token")

    try:
        if not settings.google_client_id:
            raise HTTPException(
                status_code=500,
                detail="GOOGLE_CLIENT_ID is not configured on the server",
            )

        # Verify the token against our OAuth client ID
        idinfo = id_token.verify_oauth2_token(
            payload.credential,
            requests.Request(),
            settings.google_client_id,
        )

        # Extract user info
        email = idinfo.get("email")
        name = idinfo.get("name")
        picture = idinfo.get("picture")
        google_sub = idinfo.get("sub")

        if not email:
            raise HTTPException(status_code=400, detail="Email not present in token")

        # Extra audience check defense-in-depth
        aud = idinfo.get("aud")
        if aud and aud != settings.google_client_id:
            # Extra diagnostics in server logs
            print(
                f"[AUTH] Google token audience mismatch. expected={settings.google_client_id} got={aud} email={email} sub={google_sub}"
            )
            raise HTTPException(
                status_code=401,
                detail="Invalid token audience; check GOOGLE_CLIENT_ID matches your frontend client ID.",
            )

        # Upsert user
        user = db.query(User).filter(User.email == email).first()
        if user:
            # Update profile info if changed
            user.full_name = name or user.full_name
            user.profile_picture_url = picture or user.profile_picture_url
            if google_sub:
                user.google_id = google_sub
        else:
            user = User(
                email=email,
                full_name=name,
                google_id=google_sub,
                profile_picture_url=picture,
            )
            db.add(user)
        db.commit()
        db.refresh(user)

        # Create our session JWT
        token = create_access_token(subject=str(user.id))

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


@router.get("/me", response_model=AuthUser)
def get_me(current_user: User = Depends(get_current_user)):
    return AuthUser(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        profile_picture_url=current_user.profile_picture_url,
    )
