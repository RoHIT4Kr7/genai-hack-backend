from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, date
from typing import List, Dict, Any
import json

from models.db import get_db
from utils.auth import get_current_user
from models.user import User
from models.dhyaan import DhyaanCheckin, MeditationSession
from models.manga import MangaRequest
from models.voice import VoiceSession

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _date_only(dt: datetime) -> date:
    return dt.date()


def _mood_to_score(mood_str: str) -> int:
    """Convert mood string to numeric score (1-5)"""
    mood_mapping = {
        # Negative emotions (1-2)
        "sad": 1,
        "depressed": 1,
        "hopeless": 1,
        "devastated": 1,
        "angry": 2,
        "frustrated": 2,
        "annoyed": 2,
        "upset": 2,
        "fearful": 2,
        "anxious": 2,
        "worried": 2,
        "stressed": 2,
        # Neutral emotions (3)
        "neutral": 3,
        "calm": 3,
        "peaceful": 3,
        "balanced": 3,
        "acceptance": 3,
        # Positive emotions (4-5)
        "happy": 4,
        "content": 4,
        "grateful": 4,
        "hopeful": 4,
        "confident": 4,
        "love": 4,
        "joy": 5,
        "ecstatic": 5,
        "blissful": 5,
        "energized": 5,
        "excited": 5,
    }
    return mood_mapping.get(mood_str.lower(), 3)  # Default to neutral if not found


def _get_mood_color(score: int) -> str:
    """Get color for mood score"""
    color_mapping = {
        1: "#ef4444",  # red-500 - very sad
        2: "#f97316",  # orange-500 - sad/frustrated
        3: "#eab308",  # yellow-500 - neutral
        4: "#22c55e",  # green-500 - happy
        5: "#8b5cf6",  # violet-500 - very happy
    }
    return color_mapping.get(score, "#eab308")


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

        # Mood stats (last 30 days) - collect from all sources
        cutoff = datetime.utcnow() - timedelta(days=30)

        # Get mood data from dhyaan checkins
        checkins = (
            db.query(DhyaanCheckin)
            .filter(DhyaanCheckin.user_id == current_user.id)
            .filter(DhyaanCheckin.created_at >= cutoff)
            .order_by(DhyaanCheckin.created_at.asc())
            .all()
        )

        # Get mood data from manga requests
        manga_moods = (
            db.query(MangaRequest)
            .filter(MangaRequest.user_id == current_user.id)
            .filter(MangaRequest.created_at >= cutoff)
            .order_by(MangaRequest.created_at.asc())
            .all()
        )

        # Get mood data from meditation sessions
        meditation_moods = (
            db.query(MeditationSession)
            .filter(MeditationSession.user_id == current_user.id)
            .filter(MeditationSession.created_at >= cutoff)
            .order_by(MeditationSession.created_at.asc())
            .all()
        )

        # Combine all mood data by day
        by_day: Dict[date, List[Dict[str, Any]]] = {}

        # Add dhyaan checkin moods
        for c in checkins:
            if not c.created_at:
                continue
            d = _date_only(c.created_at)
            by_day.setdefault(d, []).append(
                {
                    "score": c.mood_score,
                    "source": "checkin",
                    "color": _get_mood_color(c.mood_score),
                    "time": c.created_at,
                }
            )

        # Add manga moods
        for m in manga_moods:
            if not m.created_at:
                continue
            try:
                inputs = json.loads(m.inputs_json) if m.inputs_json else {}
                mood_str = inputs.get("inputs", {}).get("mood", "")
                if mood_str:
                    mood_score = _mood_to_score(mood_str)
                    d = _date_only(m.created_at)
                    by_day.setdefault(d, []).append(
                        {
                            "score": mood_score,
                            "source": "manga",
                            "color": _get_mood_color(mood_score),
                            "time": m.created_at,
                            "mood_text": mood_str,
                        }
                    )
            except (json.JSONDecodeError, KeyError):
                continue

        # Add meditation moods (current_feeling)
        for m in meditation_moods:
            if not m.created_at or not m.current_feeling:
                continue
            mood_score = _mood_to_score(m.current_feeling)
            d = _date_only(m.created_at)
            by_day.setdefault(d, []).append(
                {
                    "score": mood_score,
                    "source": "meditation",
                    "color": _get_mood_color(mood_score),
                    "time": m.created_at,
                    "mood_text": m.current_feeling,
                }
            )

        # Create last 30 days timeline with mood data
        timeline: List[date] = [
            (_date_only(datetime.utcnow()) - timedelta(days=i))
            for i in range(29, -1, -1)
        ]

        trend: List[Dict[str, Any]] = []
        for d in timeline:
            day_moods = by_day.get(d, [])
            if day_moods:
                # Calculate average mood for the day
                avg_score = sum(mood["score"] for mood in day_moods) / len(day_moods)
                # Get the most recent color/mood for visualization
                latest_mood = max(day_moods, key=lambda x: x["time"])
                trend.append(
                    {
                        "date": d.isoformat(),
                        "mood": round(avg_score, 1),
                        "color": latest_mood["color"],
                        "count": len(day_moods),
                        "sources": list(set(mood["source"] for mood in day_moods)),
                        "mood_details": day_moods,
                    }
                )
            else:
                trend.append(
                    {
                        "date": d.isoformat(),
                        "mood": None,
                        "color": "#6b7280",  # gray-500 for no data
                        "count": 0,
                        "sources": [],
                        "mood_details": [],
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
        elif first_avg is None and last_avg is not None:
            # If no data in first week but data in last week, show as positive improvement
            improvement_pct = round(
                (last_avg - 3) / 3 * 100, 1
            )  # Compare against neutral baseline

        # Consistency streak (consecutive days with any activity including mood tracking)
        # Build a set of dates with activity in last 60 days
        cutoff2 = datetime.utcnow() - timedelta(days=60)
        activity_dates: set[date] = set()

        # Add manga creation dates
        for r in manga_rows:
            if r.created_at and r.created_at >= cutoff2:
                activity_dates.add(_date_only(r.created_at))

        # Add meditation dates
        for r in med_rows:
            if r.created_at and r.created_at >= cutoff2:
                activity_dates.add(_date_only(r.created_at))

        # Add mood checkin dates
        for c in checkins:
            if c.created_at and c.created_at >= cutoff2:
                activity_dates.add(_date_only(c.created_at))

        # Add voice session dates
        for r in voice_rows:
            if r.started_at and r.started_at >= cutoff2:
                activity_dates.add(_date_only(r.started_at))

        # Also add dates from mood activities in the extended period
        extended_manga = (
            db.query(MangaRequest)
            .filter(MangaRequest.user_id == current_user.id)
            .filter(MangaRequest.created_at >= cutoff2)
            .all()
        )
        extended_meditation = (
            db.query(MeditationSession)
            .filter(MeditationSession.user_id == current_user.id)
            .filter(MeditationSession.created_at >= cutoff2)
            .all()
        )

        for m in extended_manga:
            if m.created_at:
                activity_dates.add(_date_only(m.created_at))

        for m in extended_meditation:
            if m.created_at:
                activity_dates.add(_date_only(m.created_at))

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
