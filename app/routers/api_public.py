"""
Public signup API: lets an external CMS (WordPress, TYPO3, Contao, or
anything else) create work-session signups without a Parcella login.

Read endpoints (upcoming sessions, parcel list) are intentionally
unauthenticated -- the same posture as the public community ICS feed in
app/ics_utils.py, and for the same reason: an external site's frontend
can't send this app's session cookie, and the data exposed (session
dates/times, plot numbers) isn't sensitive on its own.

The write endpoint (signup) requires the shared API token (see
app/public_api_auth.py) plus a lightweight honeypot and per-IP rate
limit, since -- unlike the read endpoints -- it creates data and is a
much more attractive target for abuse.

See docs/module-public-api.md for the full design rationale and the
reference WordPress connector under integrations/wordpress/.
"""
import time
import logging
from collections import defaultdict, deque
from typing import Dict, Deque

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import WorkSession, Parcel, ParcelStatus, PublicSessionSignup, PublicSessionSignupSession
from app.module_flags import require_modul
from app.public_api_auth import require_public_api_token
from app.schemas import (
    PublicWorkSessionOut, PublicParcelOut, PublicSignupCreate,
    PublicSignupResult, PublicSignupSessionResult,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/public",
    tags=["Public Signup API"],
    dependencies=[Depends(require_modul("public_signup_api"))],
)

# ---------------------------------------------------------------------------
# Simple in-memory sliding-window rate limit for the write endpoint, keyed
# by client IP. Deliberately not a new dependency (no Redis/slowapi) --
# this is a small, single-process app; a per-process in-memory limiter
# resets on deploy and doesn't share state across workers, which is an
# accepted tradeoff for a lightweight deterrent layered on top of the
# actual access control (the API token).
# ---------------------------------------------------------------------------
_RATE_LIMIT_WINDOW_SECONDS = 3600
_RATE_LIMIT_MAX_REQUESTS = 20
_recent_requests: Dict[str, Deque[float]] = defaultdict(deque)


def _check_rate_limit(client_ip: str) -> None:
    now = time.monotonic()
    window = _recent_requests[client_ip]
    while window and now - window[0] > _RATE_LIMIT_WINDOW_SECONDS:
        window.popleft()
    if len(window) >= _RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many signup requests from this address, please try again later",
        )
    window.append(now)


@router.get("/work-sessions/upcoming", response_model=list[PublicWorkSessionOut])
async def list_upcoming_sessions(db: AsyncSession = Depends(get_db)):
    from datetime import date as date_cls

    result = await db.execute(
        select(WorkSession)
        .where(WorkSession.date >= date_cls.today())
        .options(selectinload(WorkSession.participations), selectinload(WorkSession.public_signup_links))
        .order_by(WorkSession.date, WorkSession.time_from)
    )
    sessions = result.scalars().all()
    return [
        PublicWorkSessionOut(
            id=s.id, title=s.title, date=s.date,
            time_from=s.time_from, time_until=s.time_until,
            spots_left=s.available_spots,
        )
        for s in sessions
        # Hide sessions that are already full, rather than showing a
        # dead-end option a visitor could still try to check.
        if s.available_spots is None or s.available_spots > 0
    ]


@router.get("/parcels", response_model=list[PublicParcelOut])
async def list_parcels(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Parcel).where(Parcel.status == ParcelStatus.ACTIVE).order_by(Parcel.plot_number)
    )
    return result.scalars().all()


@router.post(
    "/work-sessions/signup",
    response_model=PublicSignupResult,
    dependencies=[Depends(require_public_api_token)],
)
async def submit_signup(
    payload: PublicSignupCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    # Honeypot: a real visitor never fills this field. Return a
    # believable-looking success without creating anything, so the bot
    # doesn't learn its submission was rejected.
    if payload.website:
        logger.info("Public signup honeypot triggered, silently ignoring submission")
        return PublicSignupResult(signup_id=None, results=[
            PublicSignupSessionResult(session_id=sid, accepted=True) for sid in payload.session_ids
        ])

    _check_rate_limit(request.client.host if request.client else "unknown")

    parcel_result = await db.execute(
        select(Parcel).where(Parcel.plot_number == payload.parcel_number)
    )
    parcel = parcel_result.scalar_one_or_none()
    if not parcel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown parcel number")

    sessions_result = await db.execute(
        select(WorkSession)
        .where(WorkSession.id.in_(payload.session_ids))
        .options(selectinload(WorkSession.participations), selectinload(WorkSession.public_signup_links))
    )
    sessions_by_id = {s.id: s for s in sessions_result.scalars().all()}

    signup = PublicSessionSignup(
        parcel_id=parcel.id, name=payload.name, phone=payload.phone,
        email=payload.email, remarks=payload.remarks,
    )
    db.add(signup)

    results: list[PublicSignupSessionResult] = []
    any_accepted = False
    for session_id in payload.session_ids:
        session = sessions_by_id.get(session_id)
        if not session:
            results.append(PublicSignupSessionResult(session_id=session_id, accepted=False, reason="Session not found"))
            continue
        if session.available_spots is not None and session.available_spots <= 0:
            results.append(PublicSignupSessionResult(session_id=session_id, accepted=False, reason="Session is full"))
            continue
        db.add(PublicSessionSignupSession(signup=signup, session_id=session_id))
        # Keep in-memory capacity check accurate across the loop, in case
        # the same signup lists the same limited pool twice isn't
        # possible (session_ids is a set of distinct sessions), but two
        # different sessions sharing capacity isn't a real scenario here
        # -- available_spots is per-session, so no cross-session bleed.
        results.append(PublicSignupSessionResult(session_id=session_id, accepted=True))
        any_accepted = True

    if not any_accepted:
        # Nothing valid was submitted -- don't leave an empty signup row
        # with no session links behind.
        await db.rollback()
        return PublicSignupResult(signup_id=None, results=results)

    await db.commit()
    await db.refresh(signup)
    return PublicSignupResult(signup_id=signup.id, results=results)
