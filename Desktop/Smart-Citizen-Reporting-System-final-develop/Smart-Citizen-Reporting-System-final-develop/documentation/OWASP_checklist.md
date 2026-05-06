# OWASP Top 10 Security Checklist — Smart Citizen Reporting System

**Task:** NFR-02 Security Audit & Hardening  
**Branch:** feature/NFR02-security-hardening  
**Date:** May 2026

---

## A01 — Broken Access Control

- Role-based access control (RBAC) enforced via `require_roles()` dependency
- Citizens can only access their own reports (filtered in `list_reports`, `get_report`)
- Officers/Admins only can POST comments and upload attachments
- Delete restricted to report owner (citizen) or admin only
- JWT `sub` claim mapped to user ID on every request

---

## A02 — Cryptographic Failures

- Passwords are never stored locally — authentication delegated to Supabase Auth
- JWT tokens verified via Supabase JWKS (RS256/ES256) in production
- SUPABASE_MOCK_VERIFY=false in production enforces real signature verification
- Sensitive keys (DB password, Supabase keys, HF token) stored in `.env` only
- `.env` and `.env.local` excluded from git via `.gitignore`

---

## A03 — Injection

- All database queries use SQLAlchemy ORM — no raw SQL strings
- The one `text()` call in `dependencies.py` uses parameterized binding (`:sub`, `:role`)
- Input sanitization via `bleach.clean()` strips all HTML tags before data is stored
- Pydantic validators enforce type safety and max length on all input fields

---

## A04 — Insecure Design

- Duplicate report detection prevents spam submissions
- File upload restricted to jpg/png/pdf with 5 MB max size
- AI classification runs as background task — never blocks response
- Rate limiting (slowapi) applied globally: 100 req/min per IP
- POST /reports additionally limited to 10 req/min to prevent spam

---

## A05 — Security Misconfiguration

- CORS: strict whitelist via `backend_cors_origins` — no wildcard (`*`) origins
- CORS: allowed methods restricted to GET, POST, PATCH, DELETE, OPTIONS
- CORS: allowed headers restricted to Authorization, Content-Type, Accept
- DEV_SKIP_AUTH must be set to false in production
- SUPABASE_MOCK_VERIFY must be set to false in production
- OpenAPI docs disabled in production (set openapi_url=None)

---

## A06 — Vulnerable and Outdated Components

- All dependencies pinned in `requirements.txt`
- Key libraries: FastAPI, SQLAlchemy 2.0, Pydantic v2, PyJWT with crypto
- `bleach` used for HTML sanitization (actively maintained)
- `slowapi` used for rate limiting (built on limits library)

---

## A07 — Identification and Authentication Failures

- Authentication via Supabase JWT (industry standard)
- Token verified on every request via `get_current_user` dependency
- In production: RS256/ES256 signature verified against Supabase JWKS
- Token expiry enforced by Supabase (15 min access token by default)
- No session state stored server-side — stateless JWT architecture

---

## A08 — Software and Data Integrity Failures

- Background AI pipeline failures are caught and logged — never crash the app
- File uploads saved with UUID-generated filenames (no path traversal possible)
- Database commits are atomic — notification and comment saved in single transaction
- Attachment metadata (filename, content_type, size) stored separately from file

---

## A09 — Security Logging and Monitoring

- Email addresses masked in all log output via `mask_email()` utility
- Tokens truncated to first 8 chars in logs via `mask_token()` utility
- AI pipeline logs category assignments, failures, and latency
- Duplicate detection logs warnings when duplicates are found
- Status history logged to `history` table on every status change

---

## A10 — Server-Side Request Forgery (SSRF)

- No user-supplied URLs are fetched by the backend
- File uploads saved locally — no external URL fetching
- HuggingFace and OpenAI API calls use hardcoded endpoints from config only
- Supabase JWKS URL constructed from trusted `SUPABASE_URL` config value only

---

## Summary

| OWASP Category | Status | Implementation |
|---|---|---|
| A01 Broken Access Control | ✅ | RBAC via require_roles(), citizen isolation |
| A02 Cryptographic Failures | ✅ | Supabase JWT, no local passwords, .env secrets |
| A03 Injection | ✅ | SQLAlchemy ORM, bleach sanitization, Pydantic |
| A04 Insecure Design | ✅ | Rate limiting, file validation, duplicate detection |
| A05 Security Misconfiguration | ✅ | Strict CORS, no wildcards, env flags |
| A06 Vulnerable Components | ✅ | Modern pinned dependencies |
| A07 Auth Failures | ✅ | Supabase JWT, JWKS verification, stateless |
| A08 Data Integrity | ✅ | UUID filenames, atomic transactions |
| A09 Logging & Monitoring | ✅ | Email masking, audit history table |
| A10 SSRF | ✅ | No user-supplied URL fetching |