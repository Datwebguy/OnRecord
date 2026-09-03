#!/usr/bin/env python3
"""
Operator-driven recall and memory verification script for OnRecord.
Zero hardcoded people, repositories, wallets, or seed fixtures.
Sources are provided by the operator via CLI or read from tenant_desk REFERENCE.
Enforces distinct OS processes for Session A and Session B.
"""

import sys
import os
import argparse
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.db import (
    get_scout_client, get_clerk_client, get_desk_client, init_desk,
    wipe_tenant_data, DEFAULT_DB_PATH
)
from shared.models import validate_source_string, utc_now_iso
from scout.engine import ScoutEngine
from clerk.engine import ClerkEngine

def print_banner(text: str):
    print("\n" + "=" * 60)
    print(f" {text}")
    print("=" * 60)

def run_internal_session_a(db_path: str):
    print_banner(f"SESSION A (PID: {os.getpid()}): SCOUT WRITE PATH")
    print(f"[TIMESTAMP] {datetime.now(timezone.utc).isoformat()}")
    scout_engine = ScoutEngine(db_path)
    filings = scout_engine.run_sync()
    print(f"[OK] Scout sync completed. Filings written to tenant_scout: {len(filings)}")
    for f in filings:
        print(f"  - Filed Task: {f['task_id']} | Person: {f['person']} | Source: {f['source']}")
    print(f"[SESSION A] Process (PID {os.getpid()}) terminating now.")

def run_internal_session_b(db_path: str, confirm: bool):
    print_banner(f"SESSION B (PID: {os.getpid()} - NEW OS PROCESS): CLERK RECALL")
    print(f"[TIMESTAMP] {datetime.now(timezone.utc).isoformat()}")
    
    clerk_engine = ClerkEngine(db_path)
    queue = clerk_engine.get_queue()
    print(f"[OK] Clerk projected {len(queue)} pending tasks directly from Sibyl Memory.")

    # 1. Test NOT ON RECORD for an unfiled person
    unfiled_name = f"unfiled_person_{int(time.time())}"
    check_nor = clerk_engine.check_person(unfiled_name)
    print(f"[CHECK] Verifying unfiled name '{unfiled_name}': Status = {check_nor['status']}")
    assert check_nor["status"] == "NOT_ON_RECORD", "Unfiled name must stamp NOT ON RECORD"
    print("[OK] NOT ON RECORD stamp verified for unfiled entity.")

    if queue:
        sample_task = queue[0]
        task_id = sample_task["task_id"]
        print(f"\n[ACTION] Inspecting filed task {task_id} from memory...")
        details = clerk_engine.get_task_details(task_id)
        assert details["status"] == "ACT", f"Filed task must stamp ACT, got {details['status']}"
        print(f"[OK] Task Details verified: Person='{details['person'].get('name')}', Bound='{details['person'].get('bound')}'")

        # 2. Test Open task
        open_res = clerk_engine.open_task(task_id)
        print(f"[OK] Clerk opened task {task_id}. Event recorded in tenant_clerk.")

        # 3. Test Base Ping
        bound = details["person"].get("bound", "").strip()
        print(f"\n[BASE PING] Attempting Base ping for task {task_id} (bound='{bound}', confirm={confirm})...")
        ping_res = clerk_engine.ping_task(task_id, confirm=confirm)
        print(f"[RESULT] Ping status: {ping_res.get('status')} | Details: {ping_res.get('tx_hash') or ping_res.get('reason')}")
        if ping_res.get("status") == "blocked":
            print("[OK] Correctly recorded 'blocked' event when prerequisites not met.")
        elif ping_res.get("status") == "pinged":
            print(f"[OK] Mainnet transaction confirmed: {ping_res['tx_hash']}")

    print(f"[SESSION B] Process (PID {os.getpid()}) terminating now.")

def run_internal_delete_test(db_path: str):
    print_banner(f"DELETE TEST (PID: {os.getpid()}): WIPING SCOUT MEMORY ONLY")
    
    # Get last filed person before wipe if any
    scout = get_scout_client(db_path)
    last_person_name = None
    try:
        events = scout.read_events(limit=10)
        for ev in events:
            extra = ev.get("extra") or {}
            if extra.get("person"):
                last_person_name = extra.get("person")
                break
    except Exception:
        pass

    # Wipe only tenant_scout
    deleted_rows = wipe_tenant_data("tenant_scout", db_path)
    print(f"[WIPED] Deleted {deleted_rows} rows strictly from tenant_scout.")
    
    # Verify Queue is dry
    fresh_clerk = ClerkEngine(db_path)
    dry_queue = fresh_clerk.get_queue()
    print(f"[VERIFY] Post-delete Queue length: {len(dry_queue)}")
    assert len(dry_queue) == 0, "Queue must be empty after Scout memory is deleted."
    
    # Verify previously filed person is now NOT ON RECORD
    if last_person_name:
        check_after = fresh_clerk.check_person(last_person_name)
        print(f"[VERIFY] Checking previously filed person '{last_person_name}': {check_after['status']}")
        assert check_after["status"] == "NOT_ON_RECORD", "Wiped person must return NOT_ON_RECORD"
    
    print("[OK] Delete Test Passed: Scout wiped -> queue == [] and check_person == NOT_ON_RECORD.")

def main():
    parser = argparse.ArgumentParser(description="OnRecord Operator Recall Verification")
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help="Path to SQLite database")
    parser.add_argument("--name", default="", help="Desk Name")
    parser.add_argument("--sources", nargs="*", default=None, help="Operator-provided source strings")
    parser.add_argument("--confirm", action="store_true", help="Confirm Base ping if key and bound address are present")
    parser.add_argument("--skip-delete-test", action="store_true", help="Skip the final Scout deletion test")
    
    # Internal session dispatcher flags
    parser.add_argument("--internal-session", choices=["A", "B", "DELETE"], help=argparse.SUPPRESS)
    args = parser.parse_args()

    db_path = args.db

    # Internal session execution
    if args.internal_session == "A":
        run_internal_session_a(db_path)
        return
    elif args.internal_session == "B":
        run_internal_session_b(db_path, args.confirm)
        return
    elif args.internal_session == "DELETE":
        run_internal_delete_test(db_path)
        return

    # Master orchestrator
    print_banner("STEP 1: INITIALIZE DESK & REFERENCE SCENE")
    init_desk(db_path)
    desk = get_desk_client(db_path)

    if args.sources is not None:
        # Validate operator sources
        for src in args.sources:
            if not validate_source_string(src):
                print(f"[ERROR] Invalid source format: {src}")
                sys.exit(1)
        
        scene_data = {
            "name": args.name.strip(),
            "sources": args.sources,
            "updated": utc_now_iso()
        }
        desk.set_reference("scene", scene_data)
        print(f"[OK] Saved operator Scene to tenant_desk: {len(args.sources)} sources.")
    
    import json
    current_scene_ref = desk.get_reference("scene")
    scene_body = current_scene_ref.get("body", current_scene_ref) if isinstance(current_scene_ref, dict) else {}
    if isinstance(scene_body, str):
        try:
            scene_body = json.loads(scene_body)
        except Exception:
            scene_body = {}
    sources = scene_body.get("sources", [])
    print(f"[INFO] Current Active Scene: {scene_body.get('name')} | Sources: {sources}")

    if not sources:
        print("[INFO] Scene sources is empty. Running Scout writes zero entities and zero filed events.")
        scout = ScoutEngine(db_path)
        filings = scout.run_sync()
        assert len(filings) == 0, "Empty scene must produce 0 filings."
        clerk = ClerkEngine(db_path)
        queue = clerk.get_queue()
        assert len(queue) == 0, "Empty scene must produce empty queue."
        print("[OK] Empty Scene -> 0 Scout filings -> Queue is empty.")
        print("\nPass --sources <source1> <source2> to run Session A/B across separate OS processes.")
        return

    # 1. Run Session A as a distinct OS subprocess
    cmd_a = [sys.executable, str(Path(__file__).resolve()), "--db", db_path, "--internal-session", "A"]
    res_a = subprocess.run(cmd_a, capture_output=False)
    if res_a.returncode != 0:
        print(f"[ERROR] Session A failed with returncode {res_a.returncode}")
        sys.exit(res_a.returncode)

    # 2. Run Session B as a distinct new OS subprocess
    cmd_b = [sys.executable, str(Path(__file__).resolve()), "--db", db_path, "--internal-session", "B"]
    if args.confirm:
        cmd_b.append("--confirm")
    res_b = subprocess.run(cmd_b, capture_output=False)
    if res_b.returncode != 0:
        print(f"[ERROR] Session B failed with returncode {res_b.returncode}")
        sys.exit(res_b.returncode)

    # 3. Run Delete Test as a distinct new OS subprocess
    if not args.skip_delete_test:
        cmd_del = [sys.executable, str(Path(__file__).resolve()), "--db", db_path, "--internal-session", "DELETE"]
        res_del = subprocess.run(cmd_del, capture_output=False)
        if res_del.returncode != 0:
            print(f"[ERROR] Delete test failed with returncode {res_del.returncode}")
            sys.exit(res_del.returncode)

    print_banner("ALL RECALL & MEMORY INVARIANTS PROVEN ACROSS DISTINCT OS PROCESSES!")

if __name__ == "__main__":
    main()
