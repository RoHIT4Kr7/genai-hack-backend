from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, date
from typing import List, Dict, Any

from models.db import get_db
from utils.auth import get_current_user
from models.user import User
from models.dhyaan import DhyaanCheckin, MeditationSession
from models.manga import MangaRequest
from models.voice import VoiceSession

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _date_only(dt: datetime) -> date:
    return dt.date()


@router.get("/stats")
def get_dashboard_stats(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Dict[str, Any]:
    try:
        # Recent creations (last 10 across manga and meditation)
        manga_rows = (
            db.query(MangaRequest)
            .filter(MangaRequest.user_id == current_user.id)
            .order_by(MangaRequest.created_at.desc())
            .limit(10)
            .all()
        )
        med_rows = (
            db.query(MeditationSession)
            .filter(MeditationSession.user_id == current_user.id)
            .order_by(MeditationSession.created_at.desc())
            .limit(10)
            .all()
        )
        voice_rows = (
            db.query(VoiceSession)
            .filter(VoiceSession.user_id == current_user.id)
            .order_by(VoiceSession.started_at.desc())
            .limit(10)
            .all()
        )

        recent_creations: List[Dict[str, Any]] = []
        for r in manga_rows:
            recent_creations.append(
                {
                    "type": "manga",
                    "title": r.title,
                    "story_id": r.story_id,
                    "thumbnail": r.result_url,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
            )
        for r in med_rows:
            recent_creations.append(
                {
                    "type": "meditation",
                    "title": r.title,
                    "meditation_id": r.meditation_id,
                    "thumbnail": None,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
            )
        for r in voice_rows:
            recent_creations.append(
                {
                    "type": "voice",
                    "title": "Voice Session",
                    "session_id": r.session_id,
                    "thumbnail": None,
                    "created_at": r.started_at.isoformat() if r.started_at else None,
                }
            )
        # Sort combined by created_at desc and cap to 10
        recent_creations.sort(key=lambda x: x["created_at"] or "", reverse=True)
        recent_creations = recent_creations[:10]

        # Mood stats (last 30 days)
        cutoff = datetime.utcnow() - timedelta(days=30)
        checkins = (
            db.query(DhyaanCheckin)
            .filter(DhyaanCheckin.user_id == current_user.id)
            .filter(DhyaanCheckin.created_at >= cutoff)
            .order_by(DhyaanCheckin.created_at.asc())
            .all()
        )

        # Trend by day
        trend: List[Dict[str, Any]] = []
        by_day: Dict[date, List[int]] = {}
        for c in checkins:
            if not c.created_at:
                continue
            d = _date_only(c.created_at)
            by_day.setdefault(d, []).append(c.mood_score)

        # Create last 30 days timeline, fill with daily averages where present
        timeline: List[date] = [
            (_date_only(datetime.utcnow()) - timedelta(days=i))
            for i in range(29, -1, -1)
        ]
        for d in timeline:
            scores = by_day.get(d)
            avg = sum(scores) / len(scores) if scores else None
            trend.append(
                {
                    "date": d.isoformat(),
                    "mood": avg,
                }
            )

        # Improvement %: compare average of first 7 days vs last 7 days in the 30-day window
        def _avg(vals: List[float]) -> float | None:
            vals2 = [v for v in vals if v is not None]
            return (sum(vals2) / len(vals2)) if vals2 else None

        first7 = trend[:7]
        last7 = trend[-7:]
        first_avg = _avg([t["mood"] for t in first7])
        last_avg = _avg([t["mood"] for t in last7])
        improvement_pct = None
        if first_avg is not None and last_avg is not None and first_avg > 0:
            improvement_pct = round(((last_avg - first_avg) / first_avg) * 100, 1)

        # Consistency streak (consecutive days with any activity (manga, meditation or checkin))
        # Build a set of dates with activity in last 60 days
        cutoff2 = datetime.utcnow() - timedelta(days=60)
        activity_dates: set[date] = set()
        for r in manga_rows:
            if r.created_at and r.created_at >= cutoff2:
                activity_dates.add(_date_only(r.created_at))
        for r in med_rows:
            if r.created_at and r.created_at >= cutoff2:
                activity_dates.add(_date_only(r.created_at))
        for c in checkins:
            if c.created_at and c.created_at >= cutoff2:
                activity_dates.add(_date_only(c.created_at))
        for r in voice_rows:
            if r.started_at and r.started_at >= cutoff2:
                activity_dates.add(_date_only(r.started_at))

        # Count back from today until a gap is found
        streak = 0
        cur = _date_only(datetime.utcnow())
        while cur in activity_dates:
            streak += 1
            cur = cur - timedelta(days=1)

        return {
            "consistency_streak_days": streak,
            "mood_improvement_pct": improvement_pct,
            "mood_trend_30d": trend,
            "recent_creations": recent_creations,
            "suggestion": {
                "title": "Try a short breathing session",
                "description": "A 2-minute breathing exercise can help boost your streak and mood trend today.",
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to compute dashboard stats: {e}"
        )
