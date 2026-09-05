import os
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import httpx

from shared.db import get_scout_client, get_desk_client, DEFAULT_DB_PATH
from shared.models import (
    PersonModel, AskModel, make_id, sanitize_identifier, validate_source_string
)

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class ScoutEngine:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self.scout_client = get_scout_client(db_path)
        self.desk_client = get_desk_client(db_path)

    def get_active_scene(self) -> Dict[str, Any]:
        """Scene source of truth is strictly tenant_desk REFERENCE."""
        import json
        ref = self.desk_client.get_reference("scene")
        if not ref:
            return {"name": "", "sources": [], "updated": ""}
        if isinstance(ref, dict):
            body = ref.get("body", ref)
            if isinstance(body, str):
                try:
                    body = json.loads(body)
                except Exception:
                    return {"name": "", "sources": [], "updated": ""}
            return body if isinstance(body, dict) else {"name": "", "sources": [], "updated": ""}
        return {"name": "", "sources": [], "updated": ""}

    def get_filed_event_keys(self) -> set:
        """Returns set of already filed ask_ids and source keys to avoid re-filing."""
        filed_keys = set()
        try:
            events = self.scout_client.read_events(limit=1000)
            for ev in events:
                acted = ev.get("acted") or []
                for act in acted:
                    if isinstance(act, str) and act.startswith("filed "):
                        extra = ev.get("extra") or {}
                        if "ask_id" in extra:
                            filed_keys.add(extra["ask_id"])
                        if "source" in extra:
                            filed_keys.add(extra["source"])
        except Exception:
            pass
        return filed_keys

    def fetch_github_source(self, source: str) -> List[Dict[str, Any]]:
        """
        Fetches live issues/PRs from GitHub for repo:owner/name or repo:owner/name#n.
        Zero sample or mock data.
        """
        match_issue = re.match(r"^repo:([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)#([0-9]+)$", source)
        match_repo = re.match(r"^repo:([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)$", source)

        headers = {
            "User-Agent": "OnRecord-Scout",
            "Accept": "application/vnd.github.v3+json"
        }
        token = os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"

        items = []
        try:
            with httpx.Client(timeout=10.0, headers=headers) as client:
                if match_issue:
                    owner, repo, issue_num = match_issue.groups()
                    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_num}"
                    resp = client.get(url)
                    if resp.status_code == 200:
                        data = resp.json()
                        items.append(data)
                elif match_repo:
                    owner, repo = match_repo.groups()
                    url = f"https://api.github.com/repos/{owner}/{repo}/issues?state=open&per_page=10"
                    resp = client.get(url)
                    if resp.status_code == 200:
                        data = resp.json()
                        if isinstance(data, list):
                            items.extend(data)
        except Exception:
            pass

        return items

    def run_sync(self) -> List[Dict[str, Any]]:
        """
        Executes Scout filing cycle.
        If Scene sources is empty, exits cleanly with empty filings.
        """
        scene = self.get_active_scene()
        sources = scene.get("sources", [])
        if not sources:
            return []

        filed_keys = self.get_filed_event_keys()
        new_filings = []

        for src in sources:
            src = src.strip()
            if not validate_source_string(src):
                continue

            if src.startswith("repo:"):
                gh_items = self.fetch_github_source(src)
                for item in gh_items:
                    item_id = str(item.get("id", item.get("number", "1")))
                    user = item.get("user") or {}
                    raw_login = user.get("login", "contributor")
                    person_name = sanitize_identifier(raw_login)
                    handle = raw_login
                    title = item.get("title", "Issue / Ask")
                    body_text = item.get("body") or ""
                    ask_text = f"{title}: {body_text[:200]}" if body_text else title
                    
                    seed = f"{src}_{item_id}"
                    ask_id = make_id("ask", seed)
                    task_id = make_id("task", seed)

                    if ask_id in filed_keys:
                        continue

                    # Repo-only source -> bound is strictly ""
                    person_body = {
                        "name": person_name,
                        "handle": handle,
                        "bound": "",
                        "last_ask": ask_id
                    }
                    ask_body = {
                        "id": ask_id,
                        "from": person_name,
                        "title": title,
                        "text": ask_text,
                        "source": src,
                        "filed_at": utc_now_iso()
                    }

                    # Step 1: set_entity person
                    self.scout_client.set_entity("person", person_name, person_body)
                    # Step 2: set_entity ask
                    self.scout_client.set_entity("ask", ask_id, ask_body)
                    # Step 3: write_event filed
                    self.scout_client.write_event(
                        acted=[f"filed {ask_id} person={person_name} -> {task_id}"],
                        extra={
                            "ask_id": ask_id,
                            "person": person_name,
                            "task_id": task_id,
                            "source": src,
                            "title": title
                        }
                    )
                    filed_keys.add(ask_id)
                    new_filings.append({
                        "task_id": task_id,
                        "ask_id": ask_id,
                        "person": person_name,
                        "source": src
                    })

            elif src.startswith("wallet:") or src.startswith("dune:address:"):
                # Extract address
                addr_match = re.search(r"0x[a-fA-F0-9]{40}", src)
                if not addr_match:
                    continue
                address = addr_match.group(0)
                prefix = "wallet" if src.startswith("wallet:") else "dune"
                person_name = sanitize_identifier(f"{prefix}_{address[-8:]}")
                handle = address
                bound = address

                seed = f"{src}_{address}"
                ask_id = make_id("ask", seed)
                task_id = make_id("task", seed)

                if ask_id in filed_keys:
                    continue

                text = f"Inbound activity on watched Base address {address}" if prefix == "wallet" else f"Address {address} indexed from Dune watch query"
                person_body = {
                    "name": person_name,
                    "handle": handle,
                    "bound": bound,
                    "last_ask": ask_id
                }
                ask_body = {
                    "id": ask_id,
                    "from": person_name,
                    "text": text,
                    "source": src,
                    "filed_at": utc_now_iso()
                }

                # Step 1: set_entity person
                self.scout_client.set_entity("person", person_name, person_body)
                # Step 2: set_entity ask
                self.scout_client.set_entity("ask", ask_id, ask_body)
                # Step 3: write_event filed
                self.scout_client.write_event(
                    acted=[f"filed {ask_id} person={person_name} -> {task_id}"],
                    extra={
                        "ask_id": ask_id,
                        "person": person_name,
                        "task_id": task_id,
                        "source": src
                    }
                )
                filed_keys.add(ask_id)
                new_filings.append({
                    "task_id": task_id,
                    "ask_id": ask_id,
                    "person": person_name,
                    "source": src
                })

        return new_filings
