# from __future__ import annotations

# import sys
# from pathlib import Path
# from uuid import UUID

# # Add project root to path
# sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# from sqlalchemy import func, inspect, select, text

# from app.db.base import Base
# from app.db.session import engine, SessionLocal

# from app.models.report import Report
# from app.models.user import User, UserRole
# from app.models.category import Category
# from app.models.status import Status


# # ---------------------------------------------------------------------------
# # Seed data
# # ---------------------------------------------------------------------------

# CITIZEN_ID = UUID("12345678-1234-1234-1234-123456789012")
# OFFICER_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
# ADMIN_ID = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

# USERS = [
#     User(id=CITIZEN_ID, email="citizen@example.com", role=UserRole.citizen),
#     User(id=OFFICER_ID, email="officer@example.com", role=UserRole.officer),
#     User(id=ADMIN_ID, email="admin@example.com", role=UserRole.admin),
# ]

# CATEGORIES = [
#     {"id": 1, "name": "Infrastructure"},
#     {"id": 2, "name": "Environment"},
#     {"id": 3, "name": "Safety"},
#     {"id": 4, "name": "Other"},
# ]

# STATUSES = [
#     {"id": 1, "name": "Submitted"},
#     {"id": 2, "name": "In Progress"},
#     {"id": 3, "name": "Resolved"},
#     {"id": 4, "name": "Rejected"},
#     {"id": 5, "name": "Closed"},
#     {"id": 6, "name": "Pending"},
# ]

# REPORTS = [
#     Report(
#         description="Pothole on Main Street near the bus stop.",
#         user_id=CITIZEN_ID,
#         latitude=41.9981,
#         longitude=21.4254,
#         category_id=1,   # Infrastructure
#         status_id=1,     # Submitted
#     ),
#     Report(
#         description="Broken street light on Oak Avenue.",
#         user_id=CITIZEN_ID,
#         latitude=41.9975,
#         longitude=21.4261,
#         category_id=1,   # Infrastructure
#         status_id=2,     # In Progress
#     ),
#     Report(
#         description="Graffiti on the wall of the community centre.",
#         user_id=OFFICER_ID,
#         latitude=41.9990,
#         longitude=21.4270,
#         category_id=3,   # Safety
#         status_id=3,     # Resolved
#     ),
# ]

# CATEGORIES = [
#     {"id": 1, "name": "Infrastructure"},
#     {"id": 2, "name": "Environment"},
#     {"id": 3, "name": "Safety"},
#     {"id": 4, "name": "Other"},
# ]

# STATUSES = [
#     {"id": 1, "name": "Submitted"},
#     {"id": 2, "name": "In Progress"},
#     {"id": 3, "name": "Resolved"},
#     {"id": 4, "name": "Rejected"},
#     {"id": 5, "name": "Closed"},
#     {"id": 6, "name": "Pending"},
# ]


# # ---------------------------------------------------------------------------
# # Seed function
# # ---------------------------------------------------------------------------

# # ---------------------------------------------------------------------------
# # Seed function
# # ---------------------------------------------------------------------------

# def seed() -> None:
#     print("Creating tables...")
#     Base.metadata.create_all(engine)
#     _sync_dev_schema()

#     with SessionLocal() as db:

#         # ---------------- USERS ----------------
#         existing_users = {u.id for u in db.scalars(select(User)).all()}
#         new_users = [u for u in USERS if u.id not in existing_users]

#         if new_users:
#             db.add_all(new_users)
#             db.commit()
#             print(f"Inserted {len(new_users)} user(s).")
#         else:
#             print("Users already seeded.")

#         # ---------------- CATEGORIES ----------------
#         if db.scalar(select(func.count()).select_from(Category)) == 0:
#             db.add_all([Category(**c) for c in CATEGORIES])
#             db.commit()
#             print("Inserted categories.")
#         else:
#             print("Categories already seeded.")
#             print("Users already seeded.")

#         # ---------------- REPORTS ----------------
#         # ---------------- STATUSES ----------------
#         if db.scalar(select(func.count()).select_from(Status)) == 0:
#             db.add_all([Status(**s) for s in STATUSES])
#             db.commit()
#             print("Inserted statuses.")
#         else:
#             print("Statuses already seeded.")

#         # ---------------- REPORTS ----------------
#         if db.scalar(select(func.count()).select_from(Report)) == 0:
#             db.add_all(REPORTS)
#             db.commit()
#             print(f"Inserted {len(REPORTS)} report(s).")
#         else:
#             print("Reports already seeded.")

#         # ---------------- CATEGORIES ----------------
#         if db.scalar(select(func.count()).select_from(Category)) == 0:
#             db.add_all([Category(**c) for c in CATEGORIES])
#             db.commit()
#             print("Inserted categories.")
#         else:
#             print("Categories already seeded.")

#         # ---------------- STATUSES ----------------
#         if db.scalar(select(func.count()).select_from(Status)) == 0:
#             db.add_all([Status(**s) for s in STATUSES])
#             db.commit()
#             print("Inserted statuses.")
#         else:
#             print("Statuses already seeded.")
#             print("Reports already seeded.")

#     print("Done seeding!")


# def _sync_dev_schema() -> None:
#     """
#     Apply lightweight schema repairs for local development databases.

#     SQLAlchemy `create_all()` creates missing tables, but it does not alter
#     existing tables when columns are added later in the codebase.
#     """
#     inspector = inspect(engine)
#     report_columns = {column["name"] for column in inspector.get_columns("reports")}

#     if "ai_confirmation_text" not in report_columns:
#         print("Adding missing column reports.ai_confirmation_text...")
#         with engine.begin() as conn:
#             conn.execute(text("ALTER TABLE reports ADD COLUMN ai_confirmation_text TEXT"))

#     with engine.begin() as conn:
#         report_id_default = conn.execute(
#             text("""
#                 select column_default
#                 from information_schema.columns
#                 where table_schema = 'public' and table_name = 'reports' and column_name = 'id'
#             """)
#         ).scalar_one_or_none()
#         if report_id_default is None:
#             print("Adding default gen_random_uuid() to reports.id...")
#             conn.execute(text("ALTER TABLE reports ALTER COLUMN id SET DEFAULT gen_random_uuid()"))

#         user_id_default = conn.execute(
#             text("""
#                 select column_default
#                 from information_schema.columns
#                 where table_schema = 'public' and table_name = 'users' and column_name = 'id'
#             """)
#         ).scalar_one_or_none()
#         if user_id_default is None:
#             print("Adding default gen_random_uuid() to users.id...")
#             conn.execute(text("ALTER TABLE users ALTER COLUMN id SET DEFAULT gen_random_uuid()"))


# # ---------------------------------------------------------------------------

# if __name__ == "__main__":
#     seed()
