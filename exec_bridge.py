import os
import time
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse, StreamingResponse
import uvicorn

# ---- Config ----
BASE_DIR = Path(__file__).resolve().parent
LOG_PATH = Path(os.getenv("NOOGH_COLLAB_LOG", str(BASE_DIR / "collaboration_log.md")))

# SECURITY: Token is MANDATORY in production
API_TOKEN = os.getenv("NOOGH_EXEC_TOKEN", "").strip()
IS_DEV_MODE = os.getenv("NOOGH_ENV", "production").lower() == "development"

def require_token(request: Request):
    """Enforce token check. Fail-closed in production if token is missing."""
    if not API_TOKEN:
        if IS_DEV_MODE:
            return  # Allow in dev mode without token
        raise HTTPException(status_code=503, detail="NOOGH_EXEC_TOKEN not configured")
    
    auth_header = request.headers.get("authorization", "")
    expected_auth = f"Bearer {API_TOKEN}"
    
    if auth_header == expected_auth:
        return
    
    raise HTTPException(status_code=401, detail="Unauthorized")

app = FastAPI(title="Noogh Exec Bridge", version="1.1")

@app.get("/health", response_class=PlainTextResponse)
def health():
    return "ok"

@app.get("/collab/log", response_class=PlainTextResponse)
def read_log(request: Request):
    require_token(request)  # SECURITY: Token required
    if not LOG_PATH.exists():
        return ""
    return LOG_PATH.read_text(encoding="utf-8", errors="replace")

@app.post("/collab/append", response_class=PlainTextResponse)
async def append_log(request: Request):
    require_token(request)
    body = (await request.body()).decode("utf-8", errors="replace")
    if not body.strip():
        raise HTTPException(status_code=400, detail="Empty body")

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Atomic-ish append: open in append mode, flush + fsync
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        if not body.startswith("\n"):
            f.write("\n")
        f.write(body.rstrip() + "\n")
        f.flush()
        os.fsync(f.fileno())

    return "appended"

@app.get("/sse")
async def sse(request: Request):
    """
    Streams new lines appended to collaboration_log.md.
    """
    require_token(request)  # SECURITY: Token required

    def event_stream():
            LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            LOG_PATH.touch(exist_ok=True)

            with open(LOG_PATH, "r", encoding="utf-8", errors="replace") as f:
                # Start streaming from end-of-file (tail -f behavior)
                f.seek(0, os.SEEK_END)

                while True:
                    if request.client is None:
                        logger.warning("Client is disconnected, ending stream.")
                        break

                    if hasattr(request, "is_disconnected") and request.is_disconnected:
                        logger.warning("Request is marked as disconnected, ending stream.")
                        break

                    line = f.readline()
                    if line:
                        # SSE format
                        yield f"event: logline\ndata: {line.rstrip()}\n\n"
                    else:
                        yield f": ping - {time.time()}\n\n"
                        time.sleep(5)

    return StreamingResponse(event_stream(), media_type="text/event-stream")

if __name__ == "__main__":
    # SECURITY: Default to localhost-only. Override requires explicit NOOGH_ENV=development
    default_host = "0.0.0.0" if IS_DEV_MODE else "127.0.0.1"
    host = os.getenv("NOOGH_EXEC_HOST", default_host)
    
    # Extra safety: Block public binding in production
    if host != "127.0.0.1" and not IS_DEV_MODE:
        print("⚠️  WARNING: Host override blocked in production. Use NOOGH_ENV=development to allow.")
        host = "127.0.0.1"
    
    port = int(os.getenv("NOOGH_EXEC_PORT", "9000"))
    print(f"🔒 Exec Bridge starting on {host}:{port} (Dev Mode: {IS_DEV_MODE})")
    uvicorn.run("exec_bridge:app", host=host, port=port, reload=False, log_level="info")

