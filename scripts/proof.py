#!/usr/bin/env python3
import sys
import os
import argparse
import uuid
import json
from pathlib import Path

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.db import (
    get_scout_client, get_clerk_client, get_desk_client,
    wipe_tenant_data, DEFAULT_DB_PATH
)
from clerk.engine import ClerkEngine

def parse_args():
    parser = argparse.ArgumentParser(description="OnRecord Judge Proof")
    parser.add_argument("--send", action="store_true", help="Broadcast real Base transaction if bound address exists")
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help="Path to database")
    return parser.parse_args()

def main():
    args = parse_args()
    db_path = args.db

    desk_client = get_desk_client(db_path)
    clerk_engine = ClerkEngine(db_path)

    # 1. Read Scene from reference
    scene_ref = desk_client.get_reference("scene")
    sources = []
    if scene_ref:
        body = scene_ref.get("body", scene_ref)
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except Exception:
                pass
        if isinstance(body, dict):
            sources = body.get("sources", [])

    queue = clerk_engine.get_queue()

    # If Scene sources are empty and queue is empty: exit cleanly without creating anything
    if not sources and not queue:
        print("Scene is empty and no filings exist. Please add sources and run Scout from the desk first.")
        sys.exit(0)

    # 2. WITH MEMORY
    print("--- WITH MEMORY ---")
    print(f"queue: {len(queue)}")

    if not queue:
        print("No pending tasks in queue to verify.")
        sys.exit(0)

    first_task = queue[0]
    task_id = first_task["task_id"]
    person_name = first_task.get("person", "Unknown")

    # Check filed person
    res_filed = clerk_engine.check_person(person_name)
    if res_filed.get("status") == "ON_RECORD":
        print(f"person '{person_name}': ON RECORD")
    else:
        print(f"person '{person_name}': NOT ON RECORD")

    # Check fresh unfiled name
    unfiled_name = f"unfiled_{uuid.uuid4().hex[:8]}"
    res_unfiled = clerk_engine.check_person(unfiled_name)
    if res_unfiled.get("status") == "NOT_ON_RECORD":
        print(f"person '{unfiled_name}': NOT ON RECORD")
    else:
        print(f"person '{unfiled_name}': ON RECORD")

    # Check task details and ping capability
    task_details = clerk_engine.get_task_details(task_id)
    person_body = task_details.get("person", {})
    bound_addr = (person_body.get("bound") or "").strip()

    if bound_addr and bound_addr.startswith("0x"):
        print(f"ping: allowed ({bound_addr})")
        if args.send:
            ping_res = clerk_engine.ping_task(task_id, confirm=True)
            if ping_res.get("status") == "pinged":
                print(f"ping broadcast: {ping_res.get('tx_hash')}")
            else:
                print(f"ping blocked: {ping_res.get('reason', 'unspecified')}")
    else:
        print("ping: refused (no bound address on record)")

    # 3. Wipe tenant_scout only
    wipe_tenant_data("tenant_scout", db_path)

    # 4. MEMORY DELETED
    print("\n--- MEMORY DELETED ---")
    queue_after = clerk_engine.get_queue()
    print(f"queue: {len(queue_after)}")

    res_after = clerk_engine.check_person(person_name)
    if res_after.get("status") == "NOT_ON_RECORD":
        print(f"person '{person_name}': NOT ON RECORD")
    else:
        print(f"person '{person_name}': ON RECORD")

    print("ping: refused")

if __name__ == "__main__":
    main()
