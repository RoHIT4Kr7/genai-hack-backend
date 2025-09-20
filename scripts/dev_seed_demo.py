"""
Dev helper to create a test user, mint a JWT, and seed demo records
for dashboard verification without invoking heavy generation pipelines.

Usage (PowerShell):
  .\.venv\Scripts\python.exe scripts\dev_seed_demo.py
"""

from datetime import datetime
from typing import Optional

from jose import jwt

from models.db import SessionLocal
from models.user import User
from models.manga import MangaRequest
from models.dhyaan import MeditationSession, DhyaanCheckin
from models.voice import VoiceSession
from config.settings import settings


def create_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "iat": int(datetime.utcnow().timestamp()),
        "exp": int(
            (datetime.utcnow()).timestamp() + (settings.jwt_expires_minutes * 60)
        ),
    }
    return jwt.encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )


def upsert_user(db, email: str, name: Optional[str] = None) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email, full_name=name or "Demo User")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def seed_demo(db, user_id: int):
    now = datetime.utcnow()

    # Seed a manga request (thumbnail optional)
    if not db.query(MangaRequest).filter(MangaRequest.user_id == user_id).first():
        db.add(
            MangaRequest(
                user_id=user_id,
                story_id=f"demo_story_{int(now.timestamp())}",
                inputs_json="{}",
                result_url=None,
                title="Demo Manga",
            )
        )

    # Seed a meditation session
    if (
        not db.query(MeditationSession)
        .filter(MeditationSession.user_id == user_id)
        .first()
    ):
        db.add(
            MeditationSession(
                meditation_id=f"med_{int(now.timestamp())}",
                user_id=user_id,
                current_feeling="sad",
                desired_feeling="peaceful",
                experience="beginner",
                title="Demo Meditation",
                duration=120,
                audio_url="https://example.com/audio.mp3",
                background_music_url="https://example.com/music.mp3",
                script="Take a deep breath...",
                guidance_type="breathing",
            )
        )

    # Seed a mood check-in
    db.add(
        DhyaanCheckin(
            user_id=user_id,
            mood_score=4,
            journal_entry="Feeling better today",
        )
    )

    # Seed a voice session
    if not db.query(VoiceSession).filter(VoiceSession.user_id == user_id).first():
        db.add(
            VoiceSession(
                session_id=f"voice_{int(now.timestamp())}",
                user_id=user_id,
                context="therapist_chat",
                status="active",
                started_at=now,
            )
        )

    db.commit()


def main():
    db = SessionLocal()
    try:
        user = upsert_user(db, email="demo@calmira.app", name="Calmira Demo")
        token = create_token(user.id)

        seed_demo(db, user.id)

        print("=== DEV SEED COMPLETE ===")
        print(f"User ID: {user.id}")
        print(f"Email:   {user.email}")
        print("JWT (Authorization: Bearer <token>):")
        print(token)
    finally:
        db.close()


if __name__ == "__main__":
    main()
