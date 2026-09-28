import os
import httpx
from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from .db import db, Profile

MODE = os.getenv("APP_ENV", "development")
SUPABASE = os.getenv("SUPABASE_URL", "").rstrip("/")
ANON = os.getenv("SUPABASE_ANON_KEY", "")
if MODE == "production" and (
    not SUPABASE
    or not ANON
    or not os.getenv("DATABASE_URL", "").startswith("postgresql")
):
    raise RuntimeError(
        "Production requires Supabase Auth and a PostgreSQL DATABASE_URL"
    )


async def user(
    authorization: str | None = Header(default=None), session: Session = Depends(db)
):
    if MODE == "development" and os.getenv("DEV_AUTH", "true").lower() == "true":
        p = session.get(Profile, "local-developer")
        if not p:
            p = Profile(id="local-developer", name="Local developer", role="admin")
            session.add(p)
            session.flush()
        return p
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Sign in to continue")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                SUPABASE + "/auth/v1/user",
                headers={"Authorization": authorization, "apikey": ANON},
            )
        if r.status_code != 200:
            raise HTTPException(401, "Session expired. Sign in again.")
        data = r.json()
    except httpx.HTTPError:
        raise HTTPException(503, "Authentication service unavailable")
    p = session.get(Profile, data["id"])
    if not p:
        p = Profile(
            id=data["id"],
            name=data.get("user_metadata", {}).get("name", "Learner"),
            role="student",
        )
        session.add(p)
        session.flush()
    return p


async def admin(p: Profile = Depends(user)):
    if p.role != "admin":
        raise HTTPException(403, "Administrator access required")
    return p
