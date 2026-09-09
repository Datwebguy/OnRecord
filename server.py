import os
import secrets
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Query, Body, Header, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from dotenv import load_dotenv
load_dotenv()

from shared.db import (
    get_scout_client, get_clerk_client, get_desk_client, init_desk,
    wipe_tenant_data, backup_tenant_data, restore_tenant_data, DEFAULT_DB_PATH
)
from shared.models import SceneModel, validate_source_string, utc_now_iso
from scout.engine import ScoutEngine
from clerk.engine import ClerkEngine, extract_issue_title

app = FastAPI(title="OnRecord Desk", version="1.0.0")
ADMIN_TOKEN = os.getenv("ONRECORD_ADMIN_TOKEN", "").strip()


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response

def require_admin_token(authorization: Optional[str] = Header(default=None)) -> None:
    if not ADMIN_TOKEN:
        raise HTTPException(status_code=503, detail="Operator authentication is not configured.")
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not secrets.compare_digest(token, ADMIN_TOKEN):
        raise HTTPException(status_code=401, detail="Valid operator bearer token required.")

def require_read_access(authorization: Optional[str] = Header(default=None)) -> None:
    """Protect operational reads when a deployment contains non-public records."""
    if os.getenv("ONRECORD_PROTECT_READS", "false").strip().lower() in {"1", "true", "yes", "on"}:
        require_admin_token(authorization)

def require_admin_or_judge_safe(authorization: Optional[str] = Header(default=None)) -> None:
    """Allow reproducible memory-demo mutations only in an isolated judge instance."""
    judge_mode = os.getenv("ONRECORD_JUDGE_MODE", "false").strip().lower() in {"1", "true", "yes", "on"}
    if not judge_mode:
        require_admin_token(authorization)

# Ensure static files directory exists
STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# Mount static folder
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.on_event("startup")
def startup_event():
    init_desk(DEFAULT_DB_PATH)

@app.get("/")
def read_root():
    landing_path = STATIC_DIR / "landing.html"
    if landing_path.exists():
        return FileResponse(str(landing_path))
    return FileResponse(str(STATIC_DIR / "index.html"))

@app.get("/desk")
def read_desk():
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "OnRecord Desk UI is ready."}

@app.get("/brand")
def read_brand():
    brand_path = STATIC_DIR / "brand.html"
    if brand_path.exists():
        return FileResponse(str(brand_path))
    raise HTTPException(status_code=404, detail="Brand page not found.")

@app.get("/deck")
@app.get("/presentation")
def read_deck():
    deck_path = Path(__file__).parent / "pitch_deck.html"
    if deck_path.exists():
        return FileResponse(str(deck_path))
    raise HTTPException(status_code=404, detail="Pitch deck presentation not found.")

# ==========================================
# SCENE & REFERENCE ENDPOINTS (tenant_desk)
# ==========================================

class SaveSceneRequest(BaseModel):
    name: str = ""
    sources: List[str] = Field(default_factory=list)

@app.get("/api/status")
@app.get("/healthz")
def get_status():
    judge_mode = os.getenv("ONRECORD_JUDGE_MODE", "false").strip().lower() in {"1", "true", "yes", "on"}
    return {"status": "ok", "app": "OnRecord Desk", "version": "1.0.0", "judge_mode": judge_mode}

@app.get("/api/scene", dependencies=[Depends(require_read_access)])
def get_scene():
    import json
    desk = get_desk_client(DEFAULT_DB_PATH)
    ref = desk.get_reference("scene")
    if not ref:
        return {"name": "", "sources": [], "updated": ""}
    body = ref.get("body", ref) if isinstance(ref, dict) else ref
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except Exception:
            return {"name": "", "sources": [], "updated": ""}
    return body if isinstance(body, dict) else {"name": "", "sources": [], "updated": ""}

@app.post("/api/scene", dependencies=[Depends(require_admin_or_judge_safe)])
def save_scene(req: SaveSceneRequest):
    # Validate each source strictly
    cleaned_sources = []
    for src in req.sources:
        src_clean = src.strip()
        if not src_clean:
            continue
        if not validate_source_string(src_clean):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid source string: '{src_clean}'. Allowed patterns: repo:owner/name, repo:owner/name#n, wallet:0x<40hex>@8453"
            )
        cleaned_sources.append(src_clean)

    scene_data = {
        "name": req.name.strip(),
        "sources": cleaned_sources,
        "updated": utc_now_iso()
    }

    desk = get_desk_client(DEFAULT_DB_PATH)
    desk.set_reference("scene", scene_data)
    return {"status": "saved", "scene": scene_data}

@app.get("/api/charter", dependencies=[Depends(require_read_access)])
def get_charter():
    import json
    desk = get_desk_client(DEFAULT_DB_PATH)
    ref = desk.get_reference("charter")
    if not ref:
        return {"scout": "file only", "clerk": "act only on filed tasks", "ping": "only to a Person with a bound address"}
    body = ref.get("body", ref) if isinstance(ref, dict) else ref
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=503, detail="Stored charter is invalid JSON.") from e
    return body if isinstance(body, dict) else {"scout": "file only", "clerk": "act only on filed tasks", "ping": "only to a Person with a bound address"}

@app.post("/api/desk/delete_test", dependencies=[Depends(require_admin_or_judge_safe)])
def run_delete_test(full: bool = Query(False, description="Wipe both scout and clerk partitions")):
    """
    Executes The Delete Test:
    1. Backs up tenant_scout so it can be restored on demand.
    2. Wipes tenant_scout memory partition to verify that:
       - Queue immediately drops to 0.
       - Any entity query returns NOT ON RECORD.
       - Memory is strictly load-bearing.
    """
    # Snapshot backup first
    backup_tenant_data("tenant_scout", DEFAULT_DB_PATH)
    if full:
        backup_tenant_data("tenant_clerk", DEFAULT_DB_PATH)

    deleted_scout = wipe_tenant_data("tenant_scout", DEFAULT_DB_PATH)
    deleted_clerk = 0
    if full:
        deleted_clerk = wipe_tenant_data("tenant_clerk", DEFAULT_DB_PATH)
    return {
        "status": "completed",
        "deleted_scout": deleted_scout,
        "deleted_clerk": deleted_clerk,
        "message": f"Scout memory wiped ({deleted_scout} rows deleted). Queue is now 0."
    }

@app.post("/api/desk/restore_memory", dependencies=[Depends(require_admin_or_judge_safe)])
def restore_memory():
    """
    Restores memory after a Delete Test:
    1. Restores the exact snapshot from backup (including bound wallets).
    2. Runs Scout sync to ensure all configured Scene sources are filed.
    """
    restored_snapshot = restore_tenant_data("tenant_scout", DEFAULT_DB_PATH)
    engine = ScoutEngine(DEFAULT_DB_PATH)
    filings = engine.run_sync()
    return {
        "status": "completed",
        "restored_snapshot_rows": restored_snapshot,
        "new_filings": len(filings),
        "message": f"Memory restored ({restored_snapshot} snapshot rows recovered, {len(filings)} new filings)."
    }

# ==========================================
# SCOUT ENDPOINTS (tenant_scout)
# ==========================================

@app.post("/api/scout/run", dependencies=[Depends(require_admin_or_judge_safe)])
def run_scout():
    engine = ScoutEngine(DEFAULT_DB_PATH)
    filings = engine.run_sync()
    return {"status": "completed", "filings": filings, "count": len(filings), "errors": engine.last_sync_errors}

@app.get("/api/scout/journal", dependencies=[Depends(require_read_access)])
def get_scout_journal(limit: int = Query(50, ge=1, le=100)):
    scout = get_scout_client(DEFAULT_DB_PATH)
    try:
        events = scout.read_events(limit=limit)
        for ev in events:
            extra = ev.get("extra")
            if isinstance(extra, dict) and not extra.get("title"):
                ask_id = extra.get("ask_id")
                if ask_id:
                    try:
                        ask_ent = scout.get_entity("ask", ask_id)
                        if ask_ent:
                            b = ask_ent.get("body", ask_ent)
                            extra["title"] = extract_issue_title(b)
                    except Exception:
                        pass
        return {"events": events}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Unable to read Scout journal: {e}") from e

# ==========================================
# CLERK ENDPOINTS (tenant_clerk & scout read)
# ==========================================

@app.get("/api/queue", dependencies=[Depends(require_read_access)])
@app.get("/api/clerk/queue", dependencies=[Depends(require_read_access)])
def get_queue():
    engine = ClerkEngine(DEFAULT_DB_PATH)
    queue = engine.get_queue()
    return {"queue": queue, "count": len(queue)}

@app.get("/api/clerk/check", dependencies=[Depends(require_read_access)])
def check_person(name: str = Query(..., description="Person name/handle to verify")):
    engine = ClerkEngine(DEFAULT_DB_PATH)
    result = engine.check_person(name)
    return result

@app.get("/api/clerk/task/{task_id}", dependencies=[Depends(require_read_access)])
def get_task_details(task_id: str):
    engine = ClerkEngine(DEFAULT_DB_PATH)
    details = engine.get_task_details(task_id)
    return details

class TaskActionRequest(BaseModel):
    task_id: str

@app.post("/api/clerk/open", dependencies=[Depends(require_admin_token)])
def open_task(req: TaskActionRequest):
    engine = ClerkEngine(DEFAULT_DB_PATH)
    result = engine.open_task(req.task_id)
    return result

@app.post("/api/clerk/skip", dependencies=[Depends(require_admin_token)])
def skip_task(req: TaskActionRequest):
    engine = ClerkEngine(DEFAULT_DB_PATH)
    result = engine.skip_task(req.task_id)
    return result

class BindWalletRequest(BaseModel):
    person_name: str
    address: str

@app.post("/api/clerk/bind_wallet", dependencies=[Depends(require_admin_token)])
def bind_wallet(req: BindWalletRequest):
    engine = ClerkEngine(DEFAULT_DB_PATH)
    result = engine.bind_person_wallet(req.person_name, req.address)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))
    return result

class PingTaskRequest(BaseModel):
    task_id: str
    confirm: bool = False
    tx_hash: Optional[str] = None

@app.post("/api/clerk/ping")
def ping_task(req: PingTaskRequest, authorization: Optional[str] = Header(default=None)):
    judge_mode = os.getenv("ONRECORD_JUDGE_MODE", "false").strip().lower() in {"1", "true", "yes", "on"}
    if judge_mode:
        if not req.confirm or not req.tx_hash:
            raise HTTPException(status_code=400, detail="Judge mode accepts only a browser-signed transaction hash.")
    else:
        require_admin_token(authorization)
    engine = ClerkEngine(DEFAULT_DB_PATH)
    result = engine.ping_task(
        task_id=req.task_id,
        confirm=req.confirm,
        tx_hash=req.tx_hash
    )
    return result

@app.get("/api/clerk/journal", dependencies=[Depends(require_read_access)])
def get_clerk_journal(limit: int = Query(50, ge=1, le=100)):
    clerk = get_clerk_client(DEFAULT_DB_PATH)
    try:
        events = clerk.read_events(limit=limit)
        return {"events": events}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Unable to read Clerk journal: {e}") from e
