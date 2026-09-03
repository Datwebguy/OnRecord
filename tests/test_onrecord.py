import os
import time
import secrets
import pytest
from pathlib import Path

from shared.models import (
    validate_source_string, sanitize_identifier, make_id,
    SceneModel, PersonModel, AskModel, TaskModel
)
from shared.db import (
    get_scout_client, get_clerk_client, get_desk_client, init_desk,
    wipe_tenant_data
)
from scout.engine import ScoutEngine
from clerk.engine import ClerkEngine

def test_source_validation():
    test_hex = secrets.token_hex(20)
    # Valid sources
    assert validate_source_string("repo:owner/name")
    assert validate_source_string("repo:owner-name/repo.name#123")
    assert validate_source_string(f"wallet:0x{test_hex}@8453")
    assert validate_source_string(f"wallet:0x{test_hex}")
    assert validate_source_string(f"dune:address:0x{test_hex}")

    # Invalid sources
    assert not validate_source_string("random_text")
    assert not validate_source_string("http://github.com/a/b")
    assert not validate_source_string("wallet:0x123") # too short
    assert not validate_source_string("")

def test_empty_scene(tmp_path):
    db_file = str(tmp_path / "onrecord_test.db")
    init_desk(db_file)
    
    scout = ScoutEngine(db_file)
    filings = scout.run_sync()
    assert filings == []

    clerk = ClerkEngine(db_file)
    queue = clerk.get_queue()
    assert queue == []

def test_scout_filing_and_clerk_recall(tmp_path):
    db_file = str(tmp_path / "onrecord_test.db")
    init_desk(db_file)
    desk = get_desk_client(db_file)

    # Set runtime scene with dynamically generated wallet source
    dummy_hex = secrets.token_hex(20)
    source = f"wallet:0x{dummy_hex}@8453"
    desk.set_reference("scene", {
        "name": "Test Desk",
        "sources": [source],
        "updated": "2026-09-02T00:00:00Z"
    })

    # Session A: Scout runs sync
    scout = ScoutEngine(db_file)
    filings = scout.run_sync()
    assert len(filings) == 1
    filed_task = filings[0]
    task_id = filed_task["task_id"]
    person_name = filed_task["person"]
    ask_id = filed_task["ask_id"]

    # End Session A
    del scout

    # Session B: Fresh Clerk instance
    clerk = ClerkEngine(db_file)
    
    # 1. Queue should contain the filed task
    queue = clerk.get_queue()
    assert len(queue) == 1
    assert queue[0]["task_id"] == task_id
    assert queue[0]["person"] == person_name

    # 2. Check unfiled person stamps NOT ON RECORD
    check_nor = clerk.check_person("non_existent_user_xyz")
    assert check_nor["status"] == "NOT_ON_RECORD"

    # 3. Check filed person stamps ON RECORD
    check_hit = clerk.check_person(person_name)
    assert check_hit["status"] == "ON_RECORD"
    assert check_hit["person"]["bound"] == f"0x{dummy_hex}"

    # 4. Get task details
    details = clerk.get_task_details(task_id)
    assert details["status"] == "ACT"
    assert details["person"]["name"] == person_name
    assert details["ask"]["id"] == ask_id

    # 5. Open Task
    open_res = clerk.open_task(task_id)
    assert open_res["status"] == "opened"

    # Queue should now be empty because task has an opened event in Clerk journal
    queue_after_open = clerk.get_queue()
    assert len(queue_after_open) == 0

    # 6. Base Ping without confirmation must be BLOCKED
    blocked_res = clerk.ping_task(task_id, confirm=False)
    assert blocked_res["status"] == "blocked"
    assert "confirmation required" in blocked_res["reason"].lower()

def test_empty_scene_zero_writes(tmp_path):
    db_file = str(tmp_path / "onrecord_test_empty.db")
    init_desk(db_file)
    
    scout = ScoutEngine(db_file)
    filings = scout.run_sync()
    assert filings == []

    # Assert zero entities and zero events in tenant_scout
    scout_client = get_scout_client(db_file)
    events = scout_client.read_events()
    assert events == []
    
    clerk = ClerkEngine(db_file)
    assert clerk.get_queue() == []

def test_delete_scout_empties_queue(tmp_path):
    db_file = str(tmp_path / "onrecord_test.db")
    init_desk(db_file)
    desk = get_desk_client(db_file)

    dummy_hex = secrets.token_hex(20)
    source = f"wallet:0x{dummy_hex}@8453"
    desk.set_reference("scene", {
        "name": "Delete Test Desk",
        "sources": [source],
        "updated": "2026-09-02T00:00:00Z"
    })

    scout = ScoutEngine(db_file)
    filings = scout.run_sync()
    assert len(filings) == 1
    person_name = filings[0]["person"]

    clerk = ClerkEngine(db_file)
    assert len(clerk.get_queue()) == 1
    assert clerk.check_person(person_name)["status"] == "ON_RECORD"

    # Wipe Scout tenant data only
    deleted_rows = wipe_tenant_data("tenant_scout", db_file)
    assert deleted_rows > 0

    # Fresh Clerk sees dry queue and NOT ON RECORD for the deleted person
    fresh_clerk = ClerkEngine(db_file)
    assert fresh_clerk.get_queue() == []
    assert fresh_clerk.check_person(person_name)["status"] == "NOT_ON_RECORD"
