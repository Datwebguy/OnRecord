import re
import hashlib
import time
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

SOURCE_REGEX = re.compile(
    r"^(repo:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(#[0-9]+)?|wallet:0x[a-fA-F0-9]{40}(@[0-9]+)?|dune:address:0x[a-fA-F0-9]{40})$"
)

def validate_source_string(source: str) -> bool:
    """Validate that a source string conforms to the allowed patterns."""
    return bool(SOURCE_REGEX.match(source.strip()))

def sanitize_identifier(name: str) -> str:
    """Ensure no hyphens exist in identifiers as required by Sibyl Memory."""
    return re.sub(r"[^A-Za-z0-9_]", "_", name.strip())

def make_id(prefix: str, seed: str = "") -> str:
    """Generate unhyphenated ID with prefix (e.g. ask_1a2b3c or task_1a2b3c)."""
    prefix = sanitize_identifier(prefix)
    if seed:
        digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
    else:
        digest = hashlib.sha256(f"{time.time()}_{prefix}".encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}"

class CharterModel(BaseModel):
    scout: str = "file only"
    clerk: str = "act only on filed tasks"
    ping: str = "only to a Person with a bound address"

class SceneModel(BaseModel):
    name: str = ""
    sources: List[str] = Field(default_factory=list)
    updated: str = ""

    @field_validator("sources")
    @classmethod
    def validate_sources(cls, sources: List[str]) -> List[str]:
        for src in sources:
            src_clean = src.strip()
            if not validate_source_string(src_clean):
                raise ValueError(f"Invalid source format: {src}")
        return [s.strip() for s in sources]

class PersonModel(BaseModel):
    name: str
    handle: str = ""
    bound: str = ""
    last_ask: str = ""

    def to_memory_body(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "handle": self.handle,
            "bound": self.bound,
            "last_ask": self.last_ask
        }

class AskModel(BaseModel):
    id: str
    from_user: str = Field(alias="from")
    text: str
    source: str
    filed_at: str

    def to_memory_body(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "from": self.from_user,
            "text": self.text,
            "source": self.source,
            "filed_at": self.filed_at
        }

    model_config = {"populate_by_name": True}

class TaskModel(BaseModel):
    id: str
    from_ask: str
    person: str
    allowed: List[str] = Field(default_factory=lambda: ["skip", "reply", "ping"])
    status: str = "open"

    def to_memory_body(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "from_ask": self.from_ask,
            "person": self.person,
            "allowed": self.allowed,
            "status": self.status
        }
