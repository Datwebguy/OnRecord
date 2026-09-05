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
    Preserves backup snapshots (tables starting with backup_).
    Used for the Delete Test to verify isolated failure modes.
    """
    p = Path(db_path)
    if not p.exists():
        return 0
        
    conn = sqlite3.connect(str(p))
    cursor = conn.cursor()
    
    # Find tables that do NOT start with backup_
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'backup_%';")
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

def backup_tenant_data(tenant_id: str, db_path: str = DEFAULT_DB_PATH) -> int:
    """
    Creates a snapshot backup of tenant data before a Delete Test wipe.
    Only backs up tables that contain a tenant_id column and are not internal shadow/backup tables.
    """
    p = Path(db_path)
    if not p.exists():
        return 0
    conn = sqlite3.connect(str(p))
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'backup_%' AND name NOT LIKE '%_fts%';")
    tables = [row[0] for row in cursor.fetchall()]
    backed_up = 0
    for table in tables:
        try:
            cursor.execute(f"PRAGMA table_info({table});")
            columns = [col[1] for col in cursor.fetchall()]
            if "tenant_id" not in columns:
                continue
            backup_table = f"backup_{table}"
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {backup_table} AS SELECT * FROM {table} WHERE 0;")
            cursor.execute(f"DELETE FROM {backup_table} WHERE tenant_id = ?", (tenant_id,))
            cursor.execute(f"INSERT INTO {backup_table} SELECT * FROM {table} WHERE tenant_id = ?", (tenant_id,))
            backed_up += cursor.rowcount
        except Exception:
            pass
    conn.commit()
    conn.close()
    return backed_up

def restore_tenant_data(tenant_id: str, db_path: str = DEFAULT_DB_PATH) -> int:
    """
    Restores tenant data from the backup snapshot.
    """
    p = Path(db_path)
    if not p.exists():
        return 0
    conn = sqlite3.connect(str(p))
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'backup_%' AND name NOT LIKE '%_fts%';")
    backup_tables = [row[0] for row in cursor.fetchall()]
    restored = 0
    for b_table in backup_tables:
        orig_table = b_table.replace("backup_", "")
        try:
            cursor.execute(f"INSERT OR REPLACE INTO {orig_table} SELECT * FROM {b_table} WHERE tenant_id = ?", (tenant_id,))
            restored += cursor.rowcount
        except Exception:
            pass
    conn.commit()
    conn.close()
    return restored

