#!/usr/bin/env python3
"""
OAuth Wrapper for NOOGH API Server
===================================
Provides OAuth 2.0 authentication layer on top of Bearer token auth
For integration with Perplexity and other OAuth-only clients
"""

from fastapi import FastAPI, HTTPException, Depends, Request, Form
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import secrets
import time
from typing import Optional
import uvicorn

app = FastAPI(
    title="NOOGH API OAuth Wrapper",
    version="1.0",
    description="OAuth 2.0 wrapper for NOOGH API"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
NOOGH_API_URL = "http://localhost:8888"
NOOGH_BEARER_TOKEN = "noogh-project-access-2026-x7k9m2p4"

# OAuth config (simplified)
OAUTH_CLIENT_ID = "noogh-perplexity-client"
OAUTH_CLIENT_SECRET = "noogh-secret-2026-perplexity"
OAUTH_REDIRECT_URI = "https://perplexity.ai/oauth/callback"  # Will be provided by Perplexity

# Token storage (in-memory, for demo - use Redis in production)
active_tokens = {}


@app.get("/")
async def root():
    """OAuth server info"""
    return {
        "name": "NOOGH OAuth Wrapper",
        "version": "1.0",
        "oauth_endpoints": {
            "authorize": "/oauth/authorize",
            "token": "/oauth/token",
            "userinfo": "/oauth/userinfo"
        },
        "proxy_target": NOOGH_API_URL
    }


@app.get("/oauth/authorize")
async def authorize(
    client_id: str,
    redirect_uri: str,
    response_type: str = "code",
    state: Optional[str] = None,
    scope: Optional[str] = None
):
    """
    OAuth 2.0 Authorization endpoint

    Perplexity will redirect user here to authorize
    """
    # Validate client
    if client_id != OAUTH_CLIENT_ID:
        raise HTTPException(400, "Invalid client_id")

    # Generate authorization code
    auth_code = secrets.token_urlsafe(32)

    # Store code with metadata (expires in 10 minutes)
    active_tokens[auth_code] = {
        "type": "auth_code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "expires_at": time.time() + 600,  # 10 minutes
        "used": False
    }

    # Auto-approve (in production, show consent page)
    callback_url = f"{redirect_uri}?code={auth_code}"
    if state:
        callback_url += f"&state={state}"

    return RedirectResponse(callback_url)


@app.post("/oauth/token")
async def token(
    grant_type: str = Form(...),
    code: Optional[str] = Form(None),
    redirect_uri: Optional[str] = Form(None),
    client_id: Optional[str] = Form(None),
    client_secret: Optional[str] = Form(None),
    refresh_token: Optional[str] = Form(None)
):
    """
    OAuth 2.0 Token endpoint

    Exchange authorization code for access token
    """
    # Validate client credentials
    if client_id != OAUTH_CLIENT_ID or client_secret != OAUTH_CLIENT_SECRET:
        raise HTTPException(401, "Invalid client credentials")

    if grant_type == "authorization_code":
        # Exchange code for token
        if not code or code not in active_tokens:
            raise HTTPException(400, "Invalid or expired authorization code")

        auth_data = active_tokens[code]

        # Check expiry
        if time.time() > auth_data["expires_at"]:
            del active_tokens[code]
            raise HTTPException(400, "Authorization code expired")

        # Check if already used
        if auth_data["used"]:
            raise HTTPException(400, "Authorization code already used")

        # Mark as used
        auth_data["used"] = True

        # Generate access token
        access_token = secrets.token_urlsafe(32)
        refresh_token_value = secrets.token_urlsafe(32)

        # Store access token (expires in 1 hour)
        active_tokens[access_token] = {
            "type": "access_token",
            "client_id": client_id,
            "expires_at": time.time() + 3600,  # 1 hour
            "refresh_token": refresh_token_value
        }

        # Store refresh token (expires in 30 days)
        active_tokens[refresh_token_value] = {
            "type": "refresh_token",
            "client_id": client_id,
            "access_token": access_token,
            "expires_at": time.time() + 2592000  # 30 days
        }

        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": refresh_token_value,
            "scope": "read write"
        }

    elif grant_type == "refresh_token":
        # Refresh access token
        if not refresh_token or refresh_token not in active_tokens:
            raise HTTPException(400, "Invalid refresh token")

        refresh_data = active_tokens[refresh_token]

        if time.time() > refresh_data["expires_at"]:
            del active_tokens[refresh_token]
            raise HTTPException(400, "Refresh token expired")

        # Generate new access token
        new_access_token = secrets.token_urlsafe(32)

        active_tokens[new_access_token] = {
            "type": "access_token",
            "client_id": client_id,
            "expires_at": time.time() + 3600,
            "refresh_token": refresh_token
        }

        return {
            "access_token": new_access_token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": "read write"
        }

    else:
        raise HTTPException(400, "Unsupported grant_type")


@app.get("/oauth/userinfo")
async def userinfo(request: Request):
    """
    OAuth 2.0 UserInfo endpoint

    Return user information for authenticated user
    """
    # Extract access token
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(401, "Missing or invalid Authorization header")

    access_token = auth_header.replace("Bearer ", "")

    # Validate token
    if access_token not in active_tokens:
        raise HTTPException(401, "Invalid access token")

    token_data = active_tokens[access_token]

    if token_data["type"] != "access_token":
        raise HTTPException(401, "Invalid token type")

    if time.time() > token_data["expires_at"]:
        del active_tokens[access_token]
        raise HTTPException(401, "Access token expired")

    # Return user info
    return {
        "sub": "noogh-system",
        "name": "NOOGH Trading System",
        "preferred_username": "noogh",
        "email": "noogh@trading.system"
    }


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(path: str, request: Request):
    """
    Proxy all other requests to NOOGH API

    Converts OAuth access token to Bearer token
    """
    # Extract OAuth access token
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(401, "Missing or invalid Authorization header")

    access_token = auth_header.replace("Bearer ", "")

    # Validate OAuth token
    if access_token not in active_tokens:
        raise HTTPException(401, "Invalid access token")

    token_data = active_tokens[access_token]

    if token_data["type"] != "access_token":
        raise HTTPException(401, "Invalid token type")

    if time.time() > token_data["expires_at"]:
        del active_tokens[access_token]
        raise HTTPException(401, "Access token expired")

    # Proxy request to NOOGH API with Bearer token
    url = f"{NOOGH_API_URL}/{path}"

    # Get request body
    body = await request.body()

    # Prepare headers (replace OAuth token with NOOGH Bearer token)
    headers = dict(request.headers)
    headers["Authorization"] = f"Bearer {NOOGH_BEARER_TOKEN}"
    headers.pop("host", None)  # Remove host header

    # Forward request
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                content=body,
                params=request.query_params,
                timeout=30.0
            )

            return JSONResponse(
                content=response.json() if response.headers.get("content-type", "").startswith("application/json") else {"data": response.text},
                status_code=response.status_code
            )

        except Exception as e:
            raise HTTPException(500, f"Proxy error: {str(e)}")


if __name__ == "__main__":
    print("🔐 Starting NOOGH OAuth Wrapper...")
    print(f"📡 Proxying to: {NOOGH_API_URL}")
    print(f"🔑 OAuth Client ID: {OAUTH_CLIENT_ID}")
    print(f"🔒 OAuth Client Secret: {OAUTH_CLIENT_SECRET}")
    print()
    print("OAuth Endpoints:")
    print("  - Authorization: http://localhost:8889/oauth/authorize")
    print("  - Token:         http://localhost:8889/oauth/token")
    print("  - UserInfo:      http://localhost:8889/oauth/userinfo")
    print()

    uvicorn.run(app, host="0.0.0.0", port=8889, log_level="info")
