import os
from typing import Dict, Any, List, Optional, Set
from sibyl_memory_client.exceptions import NotFoundError
from shared.db import get_scout_client, get_clerk_client, DEFAULT_DB_PATH
from shared.models import TaskModel, sanitize_identifier
from shared.base_client import execute_base_ping

class ClerkEngine:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self.scout_client = get_scout_client(db_path)
        self.clerk_client = get_clerk_client(db_path)

    # ==========================================
    # CLERK READ PATH (ZERO WRITES)
    # ==========================================

    def get_clerk_action_history(self) -> Dict[str, Dict[str, Any]]:
        """
        Reads Clerk journal to find all actions taken on task_ids.
        Returns map of task_id -> {status, event_info}.
        """
        actions: Dict[str, Dict[str, Any]] = {}
        try:
            events = self.clerk_client.read_events(limit=1000)
            for ev in events:
                acted = ev.get("acted") or []
                extra = ev.get("extra") or {}
                base_task_id = extra.get("task_id")
                
                for act in acted:
                    if not isinstance(act, str):
                        continue
                    parts = act.split()
                    verb = parts[0] if parts else ""
                    task_id = base_task_id or (parts[1] if len(parts) > 1 else None)
                    
                    if task_id and verb in ("opened", "skipped", "pinged", "blocked"):
                        # read_events is sorted by ts DESC (newest first). Keep the newest action.
                        if task_id not in actions:
                            actions[task_id] = {
                                "status": verb,
                                "event_id": ev.get("id"),
                                "ts": ev.get("ts"),
                                "act": act,
                                "extra": extra
                            }
        except Exception:
            pass
        return actions

    def get_queue(self) -> List[Dict[str, Any]]:
        """
        Computes the pending Queue dynamically:
        Tasks filed on tenant_scout with no corresponding action (opened/skipped/pinged/blocked) on tenant_clerk.
        No second database table or memory cache is used.
        """
        clerk_actions = self.get_clerk_action_history()
        queue = []
        seen_tasks: Set[str] = set()
        
        try:
            scout_events = self.scout_client.read_events(limit=1000)
            for ev in scout_events:
                acted = ev.get("acted") or []
                extra = ev.get("extra") or {}
                
                for act in acted:
                    if isinstance(act, str) and act.startswith("filed "):
                        task_id = extra.get("task_id")
                        ask_id = extra.get("ask_id")
                        person_name = extra.get("person")
                        source = extra.get("source", "")
                        
                        if not task_id:
                            # Parse from act line: filed <ask_id> person=<name> -> <task_id>
                            parts = act.split("->")
                            if len(parts) == 2:
                                task_id = parts[1].strip()

                        if task_id and task_id not in clerk_actions and task_id not in seen_tasks:
                            seen_tasks.add(task_id)
                            queue.append({
                                "task_id": task_id,
                                "ask_id": ask_id,
                                "person": person_name,
                                "source": source,
                                "filed_at": ev.get("ts")
                            })
        except Exception:
            pass
            
        return queue

    def check_person(self, name: str) -> Dict[str, Any]:
        """
        Verifies if a Person is on record in tenant_scout.
        Returns ON_RECORD with body, or stamps NOT ON RECORD on miss.
        """
        clean_name = sanitize_identifier(name)
        # 1. Direct entity lookup
        try:
            entity = self.scout_client.get_entity("person", clean_name)
            if entity:
                body = entity.get("body", entity)
                return {
                    "status": "ON_RECORD",
                    "name": clean_name,
                    "person": body
                }
        except (NotFoundError, Exception):
            pass

        # 2. Check filed records for matching handle or bound address
        try:
            events = self.scout_client.read_events(limit=1000)
            for ev in events:
                extra = ev.get("extra") or {}
                p_name = extra.get("person")
                if p_name:
                    try:
                        p_entity = self.scout_client.get_entity("person", p_name)
                        p_body = p_entity.get("body", p_entity) if p_entity else {}
                        handle = (p_body.get("handle") or "").strip()
                        bound = (p_body.get("bound") or "").strip()
                        if name.lower() in (p_name.lower(), handle.lower(), bound.lower()):
                            return {
                                "status": "ON_RECORD",
                                "name": p_name,
                                "person": p_body
                            }
                    except Exception:
                        pass
        except Exception:
            pass

        return {
            "status": "NOT_ON_RECORD",
            "name": name,
            "message": f"Person '{name}' is not filed on record in tenant_scout."
        }

    def get_task_details(self, task_id: str) -> Dict[str, Any]:
        """
        Retrieves task details strictly from what Scout filed.
        If file missing -> stamps NOT ON RECORD.
        """
        scout_events = self.scout_client.read_events(limit=1000)
        target_event = None
        for ev in scout_events:
            extra = ev.get("extra") or {}
            if extra.get("task_id") == task_id:
                target_event = ev
                break
            acted = ev.get("acted") or []
            for act in acted:
                if isinstance(act, str) and f"-> {task_id}" in act:
                    target_event = ev
                    break
            if target_event:
                break

        if not target_event:
            return {
                "status": "NOT_ON_RECORD",
                "task_id": task_id,
                "message": "Task is not filed in Scout COLD journal."
            }

        extra = target_event.get("extra") or {}
        ask_id = extra.get("ask_id")
        person_name = extra.get("person")

        # Must find both Ask and Person in Scout WARM
        try:
            ask_entity = self.scout_client.get_entity("ask", ask_id)
            ask_body = ask_entity.get("body", ask_entity)
        except (NotFoundError, Exception):
            return {
                "status": "NOT_ON_RECORD",
                "task_id": task_id,
                "message": f"Ask entity '{ask_id}' not found on record."
            }

        try:
            person_entity = self.scout_client.get_entity("person", person_name)
            person_body = person_entity.get("body", person_entity)
        except (NotFoundError, Exception):
            return {
                "status": "NOT_ON_RECORD",
                "task_id": task_id,
                "message": f"Person entity '{person_name}' not found on record."
            }

        clerk_actions = self.get_clerk_action_history()
        clerk_info = clerk_actions.get(task_id, {})
        current_status = clerk_info.get("status", "open")

        return {
            "status": "ACT",
            "task_id": task_id,
            "ask_id": ask_id,
            "ask": ask_body,
            "person": person_body,
            "clerk_status": current_status,
            "clerk_info": clerk_info,
            "allowed": ["skip", "reply", "ping"],
            "bound_address": person_body.get("bound", "")
        }

    # ==========================================
    # CLERK WRITE PATH (OPERATOR CONFIRMED)
    # ==========================================

    def open_task(self, task_id: str) -> Dict[str, Any]:
        """
        Clerk opens a filed task:
        - Writes COLD opened on tenant_clerk
        - Sets WARM task on tenant_clerk
        - Sets HOT open_task on tenant_clerk
        """
        details = self.get_task_details(task_id)
        if details.get("status") == "NOT_ON_RECORD":
            return details

        person_name = details["person"].get("name")
        ask_id = details.get("ask_id")

        # 1. Write COLD opened
        self.clerk_client.write_event(
            acted=[f"opened {task_id}"],
            extra={"task_id": task_id, "ask_id": ask_id, "person": person_name}
        )

        # 2. Set WARM task
        task_body = {
            "id": task_id,
            "from_ask": ask_id,
            "person": person_name,
            "allowed": ["skip", "reply", "ping"],
            "status": "open"
        }
        self.clerk_client.set_entity("task", task_id, task_body)

        # 3. Set HOT open_task
        self.clerk_client.set_state("open_task", {"task_id": task_id, "details": details})

        return {
            "status": "opened",
            "task_id": task_id,
            "details": details
        }

    def skip_task(self, task_id: str) -> Dict[str, Any]:
        """
        Clerk skips a filed task:
        - Writes COLD skipped on tenant_clerk
        - Updates WARM task status on tenant_clerk
        """
        details = self.get_task_details(task_id)
        if details.get("status") == "NOT_ON_RECORD":
            return details

        self.clerk_client.write_event(
            acted=[f"skipped {task_id}"],
            extra={"task_id": task_id}
        )
        
        task_body = {
            "id": task_id,
            "from_ask": details.get("ask_id", ""),
            "person": details.get("person", {}).get("name", ""),
            "allowed": ["skip", "reply", "ping"],
            "status": "skipped"
        }
        self.clerk_client.set_entity("task", task_id, task_body)

        return {"status": "skipped", "task_id": task_id}

    def ping_task(
        self,
        task_id: str,
        confirm: bool = False,
        rpc_url: Optional[str] = None,
        private_key: Optional[str] = None,
        tx_hash: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Clerk proposes and executes one confirmed Base ping to Person.bound:
        - Verifies bound address exists
        - Accepts browser wallet broadcast hash, or executes server transaction if key present
        - Writes COLD pinged with real tx hash, OR writes COLD blocked with reason
        """
        details = self.get_task_details(task_id)
        if details.get("status") == "NOT_ON_RECORD":
            return details

        bound = details.get("person", {}).get("bound", "").strip()
        if not bound:
            reason = f"Person '{details.get('person', {}).get('name')}' has no bound address (bound=''). Ping disabled."
            self.clerk_client.write_event(
                acted=[f"blocked {task_id} reason=no_bound_address"],
                extra={"task_id": task_id, "error": reason}
            )
            return {"status": "blocked", "task_id": task_id, "reason": reason}

        if not confirm:
            reason = "Operator confirmation required before executing Base ping."
            self.clerk_client.write_event(
                acted=[f"blocked {task_id} reason=no_confirmation"],
                extra={"task_id": task_id, "error": reason}
            )
            return {"status": "blocked", "task_id": task_id, "reason": reason}

        # Browser wallet broadcast pathway (MetaMask / Coinbase Wallet)
        if tx_hash and isinstance(tx_hash, str) and tx_hash.startswith("0x"):
            self.clerk_client.write_event(
                acted=[f"pinged {task_id} tx={tx_hash}"],
                extra={
                    "task_id": task_id,
                    "tx_hash": tx_hash,
                    "to": bound,
                    "chain_id": 8453,
                    "signer": "browser_wallet"
                }
            )
            task_body = {
                "id": task_id,
                "from_ask": details.get("ask_id", ""),
                "person": details.get("person", {}).get("name", ""),
                "allowed": ["skip", "reply", "ping"],
                "status": "pinged",
                "tx_hash": tx_hash
            }
            self.clerk_client.set_entity("task", task_id, task_body)
            return {
                "status": "pinged",
                "task_id": task_id,
                "tx_hash": tx_hash,
                "to": bound,
                "chain_id": 8453,
                "signer": "browser_wallet"
            }

        result = execute_base_ping(
            to_address=bound,
            task_id=task_id,
            confirm=confirm,
            rpc_url=rpc_url,
            private_key=private_key
        )

        if result.get("status") == "success":
            tx_hash = result["tx_hash"]
            self.clerk_client.write_event(
                acted=[f"pinged {task_id} tx={tx_hash}"],
                extra={
                    "task_id": task_id,
                    "tx_hash": tx_hash,
                    "to": bound,
                    "chain_id": result.get("chain_id")
                }
            )
            task_body = {
                "id": task_id,
                "from_ask": details.get("ask_id", ""),
                "person": details.get("person", {}).get("name", ""),
                "allowed": ["skip", "reply", "ping"],
                "status": "pinged",
                "tx_hash": tx_hash
            }
            self.clerk_client.set_entity("task", task_id, task_body)
            return {
                "status": "pinged",
                "task_id": task_id,
                "tx_hash": tx_hash,
                "to": bound,
                "chain_id": result.get("chain_id")
            }
        else:
            reason = result.get("reason", "Base transaction was not broadcast.")
            self.clerk_client.write_event(
                acted=[f"blocked {task_id} reason={reason}"],
                extra={"task_id": task_id, "error": reason}
            )
            return {
                "status": "blocked",
                "task_id": task_id,
                "reason": reason
            }
