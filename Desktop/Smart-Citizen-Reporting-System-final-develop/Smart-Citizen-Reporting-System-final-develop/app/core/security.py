from __future__ import annotations

import base64
import json
from functools import lru_cache
from typing import Any

from fastapi import HTTPException, status
from jwt import InvalidTokenError, PyJWKClient
import jwt

from app.core.config import get_settings


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def decode_jwt_payload(token: str) -> dict[str, Any]:
    """
    Decode a JWT payload without verifying the signature.

    IMPORTANT: This is a scaffold for local development only.
    For production, verify signatures with Supabase JWKS.
    """

    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Token is not a JWT (expected 3 dot-separated parts).")

    payload_b64 = parts[1]
    payload_bytes = _b64url_decode(payload_b64)
    payload = json.loads(payload_bytes.decode("utf-8"))

    if not isinstance(payload, dict):
        raise ValueError("Invalid JWT payload.")

    return payload


@lru_cache(maxsize=8)
def _get_jwks_client(jwks_url: str) -> PyJWKClient:
    return PyJWKClient(jwks_url)


def verify_supabase_token(token: str) -> dict[str, Any]:
    """
    Verify a Supabase JWT.

    - In dev mock mode, only decodes payload (no signature checks).
    - In real mode, verifies signature with Supabase JWKS.
    """

    settings = get_settings()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
        )

    if settings.supabase_mock_verify:
        try:
            payload = decode_jwt_payload(token)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token.",
            )
    else:
        if not settings.supabase_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SUPABASE_URL is not configured.",
            )

        base_url = settings.supabase_url.rstrip("/")
        jwks_url = f"{base_url}/auth/v1/.well-known/jwks.json"
        issuer = f"{base_url}/auth/v1"

        try:
            jwks_client = _get_jwks_client(jwks_url)
            signing_key = jwks_client.get_signing_key_from_jwt(token)

            options = {"require": ["sub", "exp", "iat"]}
            decode_kwargs: dict[str, Any] = {
                "jwt": token,
                "key": signing_key.key,
                "algorithms": ["RS256", "ES256"],
                "issuer": issuer,
                "options": options,
            }

            if settings.supabase_jwt_audience:
                decode_kwargs["audience"] = settings.supabase_jwt_audience
            else:
                options["verify_aud"] = False

            payload = jwt.decode(**decode_kwargs)
        except InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token signature or claims.",
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to verify token.",
            )

    # Minimal checks that the payload looks like an auth token.
    if "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload (missing `sub`).",
        )

    return payload

