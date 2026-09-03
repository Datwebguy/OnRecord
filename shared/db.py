import os
import json
import sqlite3
from pathlib import Path
from typing import Optional
from sibyl_memory_client import MemoryClient
from shared.models import CharterModel, SceneModel

DEFAULT_DB_PATH = "data/onrecord.db"

TENANT_SCOUT = "tenant_scout"
TENANT_CLERK = "tenant_clerk"
TENANT_DESK = "tenant_desk"

def ensure_db_dir(db_path: str = DEFAULT_DB_PATH) -> Path:
    p = Path(db_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p

def get_scout_client(db_path: str = DEFAULT_DB_PATH) -> MemoryClient:
    """Returns MemoryClient scoped strictly to tenant_scout."""
    ensure_db_dir(db_path)
    return MemoryClient.local(db_path, tenant_id=TENANT_SCOUT)

def get_clerk_client(db_path: str = DEFAULT_DB_PATH) -> MemoryClient:
    """Returns MemoryClient scoped strictly to tenant_clerk."""
    ensure_db_dir(db_path)
    return MemoryClient.local(db_path, tenant_id=TENANT_CLERK)

def get_desk_client(db_path: str = DEFAULT_DB_PATH) -> MemoryClient:
    """Returns MemoryClient scoped strictly to tenant_desk."""
    ensure_db_dir(db_path)
    return MemoryClient.local(db_path, tenant_id=TENANT_DESK)

def init_desk(db_path: str = DEFAULT_DB_PATH) -> None:
    """Ensure Charter and Scene references exist on tenant_desk without sample data."""
    desk = get_desk_client(db_path)
    
    # Check charter reference
    charter_ref = desk.get_reference("charter")
    if not charter_ref:
        charter = CharterModel()
        desk.set_reference("charter", charter.model_dump())
        
    # Check scene reference
    scene_ref = desk.get_reference("scene")
    if not scene_ref:
        scene = SceneModel(name="", sources=[], updated="")
        desk.set_reference("scene", scene.model_dump())

def wipe_tenant_data(tenant_id: str, db_path: str = DEFAULT_DB_PATH) -> int:
    """
    Wipes all rows belonging to a specific tenant in the SQLite database.
    Used for the Delete Test to verify isolated failure modes.
    """
    p = Path(db_path)
    if not p.exists():
        return 0
        
    conn = sqlite3.connect(str(p))
    cursor = conn.cursor()
    
    # Find tables that have tenant_id column
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    
    deleted_count = 0
    for table in tables:
        try:
            cursor.execute(f"DELETE FROM {table} WHERE tenant_id = ?", (tenant_id,))
            deleted_count += cursor.rowcount
        except Exception:
            pass
            
    conn.commit()
    conn.close()
    return deleted_count
