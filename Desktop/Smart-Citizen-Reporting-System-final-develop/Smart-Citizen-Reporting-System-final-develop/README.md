# Smart Citizen Complaint Management System (Backend)

FastAPI backend for managing citizen reports with **Supabase authentication** and **AI-assisted classification** (stub).

## Quickstart

### 1. Start the database

```bash
docker compose up -d
```

This starts a PostgreSQL 18 container on `localhost:5432`.

### 2. Set up the environment

```bash
python -m venv .venv
.\.venv\Scripts\activate        # Windows
# source .venv/bin/activate     # Unix

pip install -r requirements.txt
cp .env.example .env
```

The default `.env.example` already points to the Docker database — no changes needed for local dev.

### 3. Create tables and seed data

```bash
python scripts/seed.py
```

Inserts three users and sample reports. Safe to run multiple times (skips existing data).

| Email | Role | UUID |
|---|---|---|
| citizen@example.com | citizen | `12345678-1234-1234-1234-123456789012` |
| officer@example.com | officer | `aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa` |
| admin@example.com | admin | `bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb` |

### 4. Run the API

```bash
fastapi dev
```

- Swagger UI: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`
- OpenAPI JSON: `http://127.0.0.1:8000/api/v1/openapi.json`

### 5. Run tests

```bash
pytest tests/ -v
```

---

## Authentication

Routes expect `Authorization: Bearer <supabase-jwt>`. In dev mode you can skip this entirely:

**Option A — skip auth** (add to `.env`):
```
DEV_SKIP_AUTH=true
```
Every request is treated as the admin user. Remove before deploying.

**Option B — use a fake JWT** in Swagger's Authorize dialog:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3OC0xMjM0LTEyMzQtMTIzNC0xMjM0NTY3ODkwMTIiLCJlbWFpbCI6ImNpdGl6ZW5AZXhhbXBsZS5jb20iLCJhcHBfcm9sZSI6ImNpdGl6ZW4ifQ.signature
```
Signature is ignored in dev (`SUPABASE_MOCK_VERIFY=true`).

---

## Project layout

```
app/
├── main.py              # FastAPI entrypoint
├── api/router.py        # Aggregates all routers
├── core/                # Config + JWT security
├── db/                  # SQLAlchemy base, session, base_class
├── models/              # SQLAlchemy ORM models
├── schemas/             # Pydantic request/response schemas
├── routers/             # Route handlers (no business logic)
├── services/            # Business logic layer
└── utils/               # Auth dependencies + helpers
scripts/
└── seed.py              # Creates tables and inserts dev data
tests/
└── test_report_service.py
```

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5432/smart_citizen` | PostgreSQL connection string |
| `SUPABASE_MOCK_VERIFY` | `true` | Skip JWT signature check (dev only). Setting to `false` returns `501` until JWKS verification is implemented. |
| `DEV_SKIP_AUTH` | `false` | Bypass auth entirely, use hardcoded admin user |
| `PROJECT_NAME` | `Smart Citizen Complaint Management System` | Shown in OpenAPI docs |
| `API_V1_STR` | `/api/v1` | API prefix |

---

## Run with Docker

A `Dockerfile` and `docker-compose.yml` are included. The compose file brings up Postgres **and** the API:

```bash
docker compose up --build
```

- API:  http://127.0.0.1:8000/docs
- DB:   localhost:5432 (postgres/postgres/smart_citizen)

To run schema bootstrap once the stack is up:

```bash
docker compose exec app python scripts/seed.py
```

> The image bundles `transformers` and `torch` (multi-GB). Set `AI_ENABLED=false` in `.env` if you don't need classification — the model still gets pulled into the image, but the warmup is skipped and request latency drops.

---

## Deploy to Supabase

Supabase gives you Postgres + auth (JWT-based). The app treats them as two independent services so you can mix-and-match.

### Scenario A — Supabase Postgres only (dev / internal)

Use Supabase as the DB; keep the mock JWT verification. **Not safe for public deployment** — anyone can mint a JWT-shaped string and impersonate a user.

1. In the Supabase dashboard → Project Settings → Database, copy the **connection pooler** URI (transaction mode, port `6543`).
2. Add it to `.env`:
   ```dotenv
   DATABASE_URL=postgresql+psycopg://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres
   ```
   Use the **direct** URI (port `5432`) if you need to run DDL like `Base.metadata.create_all` or migrations — pooled connections drop session state.
3. Bootstrap schema (one-off, against the direct URI):
   ```bash
   python scripts/seed.py
   ```
   Edit `seed.py` first if you don't want the three demo users — typically you only seed `categories` and `statuses`, then let real users come through Supabase auth signup.
4. Keep `SUPABASE_MOCK_VERIFY=true` and/or `DEV_SKIP_AUTH=true`. Confirm `/health` returns `200` and the existing tests pass against the new DB.

### Scenario B — Full production (Supabase Postgres + Supabase auth)

Requires code work that **isn't done yet**. The path:

1. **Implement JWKS verification** in [`app/core/security.py`](app/core/security.py). The current `verify_supabase_token` returns `501` when `SUPABASE_MOCK_VERIFY=false`. Replace it with something like:

   ```python
   # pip install pyjwt[crypto]
   import jwt
   from jwt import PyJWKClient

   _jwks = PyJWKClient(settings.supabase_jwks_url, cache_keys=True)

   def verify_supabase_token(token: str) -> dict:
       signing_key = _jwks.get_signing_key_from_jwt(token).key
       return jwt.decode(
           token,
           signing_key,
           algorithms=["RS256", "ES256"],
           audience="authenticated",
           issuer=f"https://{settings.supabase_project_ref}.supabase.co/auth/v1",
       )
   ```

   The Supabase JWKS URL is `https://<project-ref>.supabase.co/auth/v1/.well-known/jwks.json`. Test the deny path (expired tokens, wrong audience, tampered payload) — this is a security boundary.

2. **Add config keys** in [`app/core/config.py`](app/core/config.py):
   ```python
   supabase_project_ref: str | None = None
   supabase_jwks_url: str | None = None
   ```

3. **Set the prod env vars** (via your hosting provider, never commit them):
   ```dotenv
   DATABASE_URL=postgresql+psycopg://postgres.<ref>:<pwd>@aws-0-<region>.pooler.supabase.com:6543/postgres
   SUPABASE_MOCK_VERIFY=false
   DEV_SKIP_AUTH=false
   SUPABASE_PROJECT_REF=<your-ref>
   SUPABASE_JWKS_URL=https://<your-ref>.supabase.co/auth/v1/.well-known/jwks.json
   ```

4. **Bootstrap schema** against the direct URI (5432):
   ```bash
   python scripts/seed.py
   ```
   Strip the `USERS` block from `seed.py` first — real users come from Supabase auth and are upserted into `app.users` on their first authenticated request.

5. **Decide on Row-Level Security (RLS)**. Supabase enables RLS by default for anything you create through their UI. Tables created via SQLAlchemy `create_all` have RLS **off**; the API itself enforces authz, so this works as long as nothing else (PostgREST, Storage, anon clients) has direct DB access via the anon key. If you intend to expose tables through Supabase's REST/realtime layer, write RLS policies — don't rely on application-layer authz alone.

6. **Storage for attachments**: [`app/utils/file_upload.py`](app/utils/file_upload.py) writes to a local `uploads/` directory and serves it from `/static/uploads`. That doesn't survive a redeploy on most PaaS hosts. Migrate to Supabase Storage (or S3) before going live.

### Production checklist

- [ ] JWKS verification implemented and tested (deny path: expired, tampered, wrong-audience tokens)
- [ ] `SUPABASE_MOCK_VERIFY=false`, `DEV_SKIP_AUTH=false`
- [ ] `DATABASE_URL` points to Supabase pooler (6543) for app traffic
- [ ] DB schema bootstrapped against direct URI (5432)
- [ ] `seed.py` doesn't insert demo users
- [ ] Reference data seeded: `categories`, `statuses` (must include a row named `Closed` for the rating flow)
- [ ] Attachments persisted off-disk (Supabase Storage / S3)
- [ ] RLS policy decision made and documented
- [ ] `.env` is **not** committed (already in `.gitignore`)
- [ ] CORS configured for your real frontend origin (not currently set in `app/main.py`)
- [ ] Health check `/health` reachable from your load balancer