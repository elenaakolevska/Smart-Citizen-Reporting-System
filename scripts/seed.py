from __future__ import annotations

import sys
from pathlib import Path
from uuid import UUID

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import func, select

from app.db.base import Base
from app.db.session import engine, SessionLocal

from app.models.report import Report
from app.models.user import User, UserRole
from app.models.category import Category
from app.models.status import Status


# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

CITIZEN_ID = UUID("12345678-1234-1234-1234-123456789012")
OFFICER_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
ADMIN_ID = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

USERS = [
    User(id=CITIZEN_ID, email="citizen@example.com", role=UserRole.citizen),
    User(id=OFFICER_ID, email="officer@example.com", role=UserRole.officer),
    User(id=ADMIN_ID, email="admin@example.com", role=UserRole.admin),
]

CATEGORIES = [
    {"id": 1, "name": "Infrastructure"},
    {"id": 2, "name": "Environment"},
    {"id": 3, "name": "Safety"},
    {"id": 4, "name": "Other"},
]

STATUSES = [
    {"id": 1, "name": "Submitted"},
    {"id": 2, "name": "In Progress"},
    {"id": 3, "name": "Resolved"},
    {"id": 4, "name": "Rejected"},
    {"id": 5, "name": "Closed"},
    {"id": 6, "name": "Pending"},
]

REPORTS = [
    Report(
        description="Pothole on Main Street near the bus stop.",
        user_id=CITIZEN_ID,
        latitude=41.9981,
        longitude=21.4254,
        category_id=1,   # Infrastructure
        status_id=1,     # Submitted
        priority="high",
    ),
    Report(
        description="Broken street light on Oak Avenue.",
        user_id=CITIZEN_ID,
        latitude=41.9975,
        longitude=21.4261,
        category_id=1,   # Infrastructure
        status_id=2,     # In Progress
        priority="medium",
    ),
    Report(
        description="Graffiti on the wall of the community centre.",
        user_id=OFFICER_ID,
        latitude=41.9990,
        longitude=21.4270,
        category_id=3,   # Safety
        status_id=3,     # Resolved
        priority="low",
    ),
    Report(
        description="Overgrown bushes blocking the sidewalk on Bulevar Partizanski Odredi.",
        user_id=CITIZEN_ID,
        latitude=41.9985,
        longitude=21.4150,
        category_id=2,   # Environment
        status_id=5,     # Closed
        priority="medium",
    ),
    Report(
        description="Water leak from a pipe near the primary school.",
        user_id=CITIZEN_ID,
        latitude=42.0010,
        longitude=21.4300,
        category_id=1,   # Infrastructure
        status_id=5,     # Closed
        priority="high",
        rating=5,
        rating_comment="Брзо и ефикасно решено!",
    ),
]

CATEGORIES = [
    {"id": 1, "name": "Infrastructure"},
    {"id": 2, "name": "Environment"},
    {"id": 3, "name": "Safety"},
    {"id": 4, "name": "Other"},
]

STATUSES = [
    {"id": 1, "name": "Submitted"},
    {"id": 2, "name": "In Progress"},
    {"id": 3, "name": "Resolved"},
    {"id": 4, "name": "Rejected"},
    {"id": 5, "name": "Closed"},
    {"id": 6, "name": "Pending"},
]


# ---------------------------------------------------------------------------
# Seed function
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Seed function
# ---------------------------------------------------------------------------

def seed() -> None:
    print("Creating tables...")
    Base.metadata.create_all(engine)

    with SessionLocal() as db:

        # ---------------- USERS ----------------
        existing_users = {u.id for u in db.scalars(select(User)).all()}
        new_users = [u for u in USERS if u.id not in existing_users]

        if new_users:
            db.add_all(new_users)
            db.commit()
            print(f"Inserted {len(new_users)} user(s).")
        else:
            print("Users already seeded.")

        # ---------------- CATEGORIES ----------------
        if db.scalar(select(func.count()).select_from(Category)) == 0:
            db.add_all([Category(**c) for c in CATEGORIES])
            db.commit()
            print("Inserted categories.")
        else:
            print("Categories already seeded.")
            print("Users already seeded.")

        # ---------------- REPORTS ----------------
        # ---------------- STATUSES ----------------
        if db.scalar(select(func.count()).select_from(Status)) == 0:
            db.add_all([Status(**s) for s in STATUSES])
            db.commit()
            print("Inserted statuses.")
        else:
            print("Statuses already seeded.")

        # ---------------- REPORTS ----------------
        if db.scalar(select(func.count()).select_from(Report)) == 0:
            db.add_all(REPORTS)
            db.commit()
            print(f"Inserted {len(REPORTS)} report(s).")
        else:
            print("Reports already seeded.")

        # ---------------- CATEGORIES ----------------
        if db.scalar(select(func.count()).select_from(Category)) == 0:
            db.add_all([Category(**c) for c in CATEGORIES])
            db.commit()
            print("Inserted categories.")
        else:
            print("Categories already seeded.")

        # ---------------- STATUSES ----------------
        if db.scalar(select(func.count()).select_from(Status)) == 0:
            db.add_all([Status(**s) for s in STATUSES])
            db.commit()
            print("Inserted statuses.")
        else:
            print("Statuses already seeded.")
            print("Reports already seeded.")

    print("Done seeding!")


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    seed()