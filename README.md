# OnRecord

> **Scout files. Clerk only acts on what is on record.**

OnRecord is a two-agent desk for incoming work. Work moves strictly as filed records across isolated memory partitions, and the irreversible onchain step requires explicit human operator confirmation.

```
You (Operator)
  │  set Scene at runtime, confirm the one hard action
  ▼
Scout (tenant_scout)           Clerk (tenant_clerk)
read + file                    act only on files
     │                              ▲
     └─────────── handoff ──────────┘
                  COLD event
             no row = no action
```

---

## Where Sibyl Memory is Load-Bearing (Judge Fast-Path)

Sibyl Memory sits on the critical execution path of OnRecord. Isolation is the product: all three tenants (`tenant_scout`, `tenant_clerk`, `tenant_desk`) share a single database (`data/onrecord.db`), but neither agent can access or mutate the other's brain.

Judges can inspect the exact memory calls in under 2 minutes:

### 1. Scout Write Path
File: [`scout/engine.py`](file:///c:/Users/DELL/Downloads/OnRecord/scout/engine.py)
- **Filing Logic**: Scout files asks it finds (e.g. inbound activity on a watched wallet or actual retrieved issue authors on a repo), not the repository owner by default. Wallet sources file directly with `bound` address.
- **`set_entity` (WARM Person)**: `scout_client.set_entity("person", person_name, person_body)`
- **`set_entity` (WARM Ask)**: `scout_client.set_entity("ask", ask_id, ask_body)`
- **`write_event` (COLD Event Handoff)**: `scout_client.write_event(acted=[f"filed {ask_id} person={person_name} -> {task_id}"], extra={"ask_id": ask_id, "person": person_name, "task_id": task_id, "source": src})`

### 2. Clerk Read Path (Zero Writes)
File: [`clerk/engine.py`](file:///c:/Users/DELL/Downloads/OnRecord/clerk/engine.py)
- **`get_queue`**: `scout_client.read_events(limit=1000)` filters for `acted` starting with `"filed "`. Cross-checks against `clerk_client.read_events(limit=1000)` to project pending tasks dynamically. No secondary database table or cached memory is used.
- **`check_person` (`NOT ON RECORD`)**: `scout_client.get_entity("person", name)`. If the record was never filed, Clerk halts and stamps **`NOT ON RECORD`**.

### 3. Clerk Write Path (Action on Record)
File: [`clerk/engine.py`](file:///c:/Users/DELL/Downloads/OnRecord/clerk/engine.py)
- **`open_task`**: `clerk_client.write_event(acted=[f"opened {task_id}"], ...)`, sets WARM `task`, and sets HOT state `open_task`.
- **`skip_task`**: `clerk_client.write_event(acted=[f"skipped {task_id}"], ...)`.
- **`ping_task`**: `clerk_client.write_event(acted=[f"pinged {task_id} tx={tx_hash}"], ...)` or `clerk_client.write_event(acted=[f"blocked {task_id} reason={reason}"], ...)`.

---

## Where Base is Used

- **Network**: Base Mainnet (Chain ID `8453`, RPC `https://mainnet.base.org`).
- **Bound Addresses**: `Person.bound` is populated exclusively from operator-specified `wallet:` or `dune:address:` sources. Repo-only sources have `bound=""` and cannot be pinged.
- **Operator Confirmation**: Clerk never pings autonomously. The operator must check the confirmation box and supply `BASE_PRIVATE_KEY` for an onchain transaction to broadcast.
- **Authentic Hashes**: If unconfirmed or missing a signing key, Clerk logs a `blocked` COLD event. Fake hashes and simulation previews are strictly rejected.
- Implementation: [`shared/base_client.py`](file:///c:/Users/DELL/Downloads/OnRecord/shared/base_client.py) (`execute_base_ping`) and [`clerk/engine.py`](file:///c:/Users/DELL/Downloads/OnRecord/clerk/engine.py) (`ping_task`).

---

## Architecture & Memory Stores

| Store | Tenant | Role | Purpose |
|---|---|---|---|
| **WARM** | `tenant_scout` | Scout | `Person`, `Repo`, `Ask` entities |
| **COLD** | `tenant_scout` | Scout | Append-only event journal (`filed ...`) |
| **WARM** | `tenant_clerk` | Clerk | `Task` entities |
| **COLD** | `tenant_clerk` | Clerk | Action journal (`opened`, `skipped`, `pinged`, `blocked`) |
| **REFERENCE** | `tenant_desk` | Operator | Policy `Charter` and runtime `Scene` sources |
| **HOT** | `tenant_clerk` | Clerk | `open_task` active state |

---

## Zero Hardcoded Data Policy

- `scene.json` ships empty (`"sources": []`).
- No preloaded people, wallets, repository constants, or sample cards exist in the repo or runtime defaults.
- All IDs (`ask_<hash>`, `task_<hash>`) are generated dynamically from live operator inputs.
- Empty Scene $\rightarrow$ 0 Scout filings $\rightarrow$ Empty Queue.

---

## Quickstart

### 1. Run the Desk Server
```bash
uvicorn server:app --port 8000
```
Open [http://localhost:8000](http://localhost:8000) in your browser.

### 2. Operator Workflow
1. **Scene Form**: Enter a Desk Name and paste your own sources (e.g. `repo:owner/name` or `wallet:0x<your address>@8453`). Click **Save Scene**.
2. **Run Scout**: Click **Run Scout**. Scout queries live endpoints and files records into `tenant_scout`.
3. **Queue & Clerk**: Filed tasks appear in the Queue column. Click a task to view the Person Card and Ask.
4. **Verifier**: Use the Clerk Verifier input to test any person name. If not filed by Scout, it stamps **`NOT ON RECORD`**.
5. **Base Ping**: For tasks with a bound address, check the confirmation box and click **Confirm & Send Ping** to broadcast on Base.

---

## Recall & Delete Verification

### In-Browser Recall
1. Start the server: `uvicorn server:app --port 8000`.
2. Add your source and click **Run Scout** (Session A).
3. Stop the `uvicorn` process completely (`Ctrl+C`).
4. Start `uvicorn server:app --port 8000` again (Session B).
5. Refresh the page: the filed tasks and history are instantly loaded from `data/onrecord.db` with zero chat context or in-memory state.

### Automated Script Recall
Optionally run the multi-process verification runner passing your own live source:

```bash
# Empty Scene check (asserts 0 filings and empty queue)
python scripts/recall.py

# Multi-process recall with your own source
python scripts/recall.py --name "Desk" --sources repo:owner/name wallet:0xYOURADDRESS@8453
```

### The Delete Test (How Memory Made This Possible)
When `tenant_scout` memory is deleted:
1. The Queue dries up immediately (`queue = []`).
2. Clerk has nothing to open and cannot recall previous identities (`check_person` returns `NOT_ON_RECORD`).
3. Live chain and GitHub sources continue to exist, but OnRecord's desk is cleanly reset.

---

## Prior Work

OnRecord builds on the principles of:
- **Sibyl Memory**: Multi-tenant partitioned memory for agent architectures.
- **Base**: Ethereum Layer-2 for verified onchain settlement and pings.
- **Event Sourcing & CQRS**: Projecting task queues dynamically from append-only COLD journals without redundant mutable tables.
- **Least-Privilege Role Separation**: Separating read/file agents (Scout) from action agents (Clerk), with irrevocable actions mediated by human operators.

---

## License

[MIT](LICENSE)
