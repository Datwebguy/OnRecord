import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from dotenv import load_dotenv
load_dotenv()

from shared.db import (
    get_scout_client, get_clerk_client, get_desk_client, init_desk, DEFAULT_DB_PATH
)
from shared.models import SceneModel, validate_source_string, utc_now_iso
from scout.engine import ScoutEngine
from clerk.engine import ClerkEngine

app = FastAPI(title="OnRecord Desk", version="1.0.0")

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

# ==========================================
# SCENE & REFERENCE ENDPOINTS (tenant_desk)
# ==========================================

class SaveSceneRequest(BaseModel):
    name: str = ""
    sources: List[str] = Field(default_factory=list)

@app.get("/api/scene")
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

@app.post("/api/scene")
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
                detail=f"Invalid source string: '{src_clean}'. Allowed patterns: repo:owner/name, repo:owner/name#n, wallet:0x<40hex>@8453, dune:address:0x<40hex>"
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

@app.get("/api/charter")
def get_charter():
    desk = get_desk_client(DEFAULT_DB_PATH)
    ref = desk.get_reference("charter")
    if not ref:
        return {"scout": "file only", "clerk": "act only on filed tasks", "ping": "only to a Person with a bound address"}
    body = ref.get("body", ref) if isinstance(ref, dict) else ref
    return body

# ==========================================
# SCOUT ENDPOINTS (tenant_scout)
# ==========================================

@app.post("/api/scout/run")
def run_scout():
    engine = ScoutEngine(DEFAULT_DB_PATH)
    filings = engine.run_sync()
    return {"status": "completed", "filings": filings, "count": len(filings)}

@app.get("/api/scout/journal")
def get_scout_journal(limit: int = 50):
    scout = get_scout_client(DEFAULT_DB_PATH)
    try:
        events = scout.read_events(limit=limit)
        return {"events": events}
    except Exception as e:
        return {"events": [], "error": str(e)}

# ==========================================
# CLERK ENDPOINTS (tenant_clerk & scout read)
# ==========================================

@app.get("/api/queue")
def get_queue():
    engine = ClerkEngine(DEFAULT_DB_PATH)
    queue = engine.get_queue()
    return {"queue": queue, "count": len(queue)}

@app.get("/api/clerk/check")
def check_person(name: str = Query(..., description="Person name/handle to verify")):
    engine = ClerkEngine(DEFAULT_DB_PATH)
    result = engine.check_person(name)
    return result

@app.get("/api/clerk/task/{task_id}")
def get_task_details(task_id: str):
    engine = ClerkEngine(DEFAULT_DB_PATH)
    details = engine.get_task_details(task_id)
    return details

class TaskActionRequest(BaseModel):
    task_id: str

@app.post("/api/clerk/open")
def open_task(req: TaskActionRequest):
    engine = ClerkEngine(DEFAULT_DB_PATH)
    result = engine.open_task(req.task_id)
    return result

@app.post("/api/clerk/skip")
def skip_task(req: TaskActionRequest):
    engine = ClerkEngine(DEFAULT_DB_PATH)
    result = engine.skip_task(req.task_id)
    return result

class PingTaskRequest(BaseModel):
    task_id: str
    confirm: bool = False
    rpc_url: Optional[str] = None
    private_key: Optional[str] = None
    tx_hash: Optional[str] = None

@app.post("/api/clerk/ping")
def ping_task(req: PingTaskRequest):
    engine = ClerkEngine(DEFAULT_DB_PATH)
    result = engine.ping_task(
        task_id=req.task_id,
        confirm=req.confirm,
        rpc_url=req.rpc_url,
        private_key=req.private_key,
        tx_hash=req.tx_hash
    )
    return result

@app.get("/api/clerk/journal")
def get_clerk_journal(limit: int = 50):
    clerk = get_clerk_client(DEFAULT_DB_PATH)
    try:
        events = clerk.read_events(limit=limit)
        return {"events": events}
    except Exception as e:
        return {"events": [], "error": str(e)}
