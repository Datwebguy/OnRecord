import os
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import httpx
from web3 import Web3

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
        self.last_sync_errors: List[str] = []

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
                    elif resp.status_code >= 400:
                        self.last_sync_errors.append(
                            f"GitHub source {source} returned HTTP {resp.status_code}."
                        )
        except Exception:
            self.last_sync_errors.append(f"GitHub source {source} could not be reached.")

        return items

    def fetch_base_wallet_activity(self, source: str) -> List[Dict[str, Any]]:
        """Read recent ERC-20 Transfer logs involving a Base wallet via JSON-RPC."""
        match = re.match(r"^wallet:(0x[a-fA-F0-9]{40})(?:@([0-9]+))?$", source)
        if not match:
            return []
        address, chain = match.groups()
        if chain and int(chain) != 8453:
            self.last_sync_errors.append(f"Wallet source {source} is not on Base Mainnet (8453).")
            return []

        rpc_url = os.getenv("BASE_RPC_URL", "https://mainnet.base.org")
        try:
            with httpx.Client(timeout=15.0) as client:
                chain_id = client.post(rpc_url, json={"jsonrpc": "2.0", "id": 1, "method": "eth_chainId", "params": []}).json().get("result")
                if chain_id != "0x2105":
                    self.last_sync_errors.append(f"Base RPC reported chain {chain_id!r}; expected 0x2105.")
                    return []
                latest = int(client.post(rpc_url, json={"jsonrpc": "2.0", "id": 2, "method": "eth_blockNumber", "params": []}).json()["result"], 16)
                window = max(1, min(int(os.getenv("BASE_SCAN_BLOCKS", "2000")), 10000))
                padded = "0x" + address[2:].lower().zfill(64)
                transfer_topic = Web3.keccak(text="Transfer(address,address,uint256)").hex()
                params = {
                    "fromBlock": hex(max(0, latest - window)),
                    "toBlock": hex(latest),
                    "topics": [transfer_topic, None, padded],
                }
                response = client.post(rpc_url, json={"jsonrpc": "2.0", "id": 3, "method": "eth_getLogs", "params": [params]})
                payload = response.json()
                if response.status_code >= 400 or payload.get("error"):
                    self.last_sync_errors.append(f"Base wallet source {source} returned an RPC error.")
                    return []
                return [
                    {
                        "id": f"{log.get('transactionHash')}:{int(log.get('logIndex', '0x0'), 16)}",
                        "title": "Base ERC-20 transfer",
                        "body": f"Observed ERC-20 Transfer in block {int(log.get('blockNumber', '0x0'), 16)}.",
                        "user": {"login": address},
                    }
                    for log in payload.get("result", [])
                ]
        except Exception as exc:
            self.last_sync_errors.append(f"Base wallet source {source} could not be reached: {exc}")
            return []

    def run_sync(self) -> List[Dict[str, Any]]:
        """
        Executes Scout filing cycle.
        If Scene sources is empty, exits cleanly with empty filings.
        """
        self.last_sync_errors = []
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
                self._file_items(src, gh_items, filed_keys, new_filings)
            elif src.startswith("wallet:"):
                self._file_items(src, self.fetch_base_wallet_activity(src), filed_keys, new_filings, bound_from_source=True)
        return new_filings

    def _file_items(self, src: str, items: List[Dict[str, Any]], filed_keys: set,
                    new_filings: List[Dict[str, Any]], bound_from_source: bool = False) -> None:
        """Persist only evidence returned by a source adapter."""
        addr_match = re.search(r"0x[a-fA-F0-9]{40}", src)
        bound = addr_match.group(0) if bound_from_source and addr_match else ""
        for item in items:
            item_id = str(item.get("id", item.get("number", ""))).strip()
            if not item_id:
                continue
            user = item.get("user") or {}
            raw_login = user.get("login", "contributor")
            person_name = sanitize_identifier(raw_login)
            title = item.get("title", "Issue / Ask")
            body_text = item.get("body") or ""
            ask_text = f"{title}: {body_text[:200]}" if body_text else title
            seed = f"{src}_{item_id}"
            ask_id = make_id("ask", seed)
            task_id = make_id("task", seed)
            if ask_id in filed_keys:
                continue
            person_body = {"name": person_name, "handle": raw_login, "bound": bound, "last_ask": ask_id}
            ask_body = {"id": ask_id, "from": person_name, "title": title, "text": ask_text, "source": src, "filed_at": utc_now_iso()}
            self.scout_client.set_entity("person", person_name, person_body)
            self.scout_client.set_entity("ask", ask_id, ask_body)
            self.scout_client.write_event(
                acted=[f"filed {ask_id} person={person_name} -> {task_id}"],
                extra={"ask_id": ask_id, "person": person_name, "task_id": task_id, "source": src, "title": title}
            )
            filed_keys.add(ask_id)
            new_filings.append({"task_id": task_id, "ask_id": ask_id, "person": person_name, "source": src})
