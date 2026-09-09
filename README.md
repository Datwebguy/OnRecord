<div align="center">

# OnRecord

**Scout files. Clerk only acts on what is on record.**

<br/>

<img src="https://img.shields.io/badge/Network-Base%20Mainnet%20(8453)-0052FF?style=for-the-badge&logo=coinbase&logoColor=white" alt="Base Mainnet" />
<img src="https://img.shields.io/badge/Storage-Sibyl%20Memory%20Client-8A2BE2?style=for-the-badge" alt="Sibyl Memory" />
<img src="https://img.shields.io/badge/Architecture-Two%20Role%20Desk-C4A35A?style=for-the-badge" alt="Architecture" />
<img src="https://img.shields.io/badge/License-MIT-C81E1E?style=for-the-badge" alt="License" />

</div>

OnRecord is an audit-proof operational desk for incoming work. Autonomous agent systems frequently collapse when downstream execution relies on unverified conversation memory rather than durable state. When an agent acts on assumptions that were never filed into memory, records drift, tasks duplicate, and actions execute without accountability. OnRecord solves this by separating observation from execution across isolated memory partitions: Scout monitors incoming channels and files work into storage, Clerk verifies records and inspects pending tasks, and the human operator retains exclusive confirmation authority over irreversible onchain settlement on Base.

```
       Operator Allowlist (Scene Reference)
                        │
                        ▼
      ┌───────────────────────────────────┐
      │       SCOUT (tenant_scout)        │
      │   Observes Repositories & Wallets │
      │   Files Person & Ask to WARM      │
      │   Zero Signing Key · Zero Spend   │
      └─────────────────┬─────────────────┘
                        │
                 COLD Event Handoff
           ("filed ask_... -> task_...")
                        │
                        ▼
      ┌───────────────────────────────────┐
      │       CLERK (tenant_clerk)        │
      │   Projects Backlog from Events    │
      │   Verifies Entities in Storage    │
      │   Missing Record = NOT ON RECORD  │
      └─────────────────┬─────────────────┘
                        │
             Human Operator Confirmation
                        │
                        ▼
      ┌───────────────────────────────────┐
      │       BASE MAINNET (8453)         │
      │   Authentic Onchain Settlement    │
      └───────────────────────────────────┘
```

---

## Where Sibyl Memory is Load-Bearing (Judge Fast-Path)

Sibyl Memory serves as the foundational execution spine of OnRecord. The platform utilizes the official `sibyl-memory-client` library configured against a local SQLite storage engine located at `data/onrecord.db`. The system enforces strict multi-tenant isolation, partitioning the memory store into three distinct tenant spaces: `tenant_scout`, `tenant_clerk`, and `tenant_desk`. While all tenants share the physical database, each agent role is strictly scoped to its assigned tenant namespace and cannot directly mutate the internal state of another.

Judges can inspect the primary memory call sites across the codebase:

### 1. Scout Ingestion & Write Path
Located in [`scout/engine.py`](scout/engine.py):

Scout reads allowed sources configured by the operator in `tenant_desk` reference storage. When inbound activity is detected, Scout populates canonical entity files inside its WARM tier via `scout_client.set_entity("person", person_name, person_body)` and `scout_client.set_entity("ask", ask_id, ask_body)`. Scout then commits an append-only event to its COLD tier using `scout_client.write_event(acted=[f"filed {ask_id} person={person_name} -> {task_id}"], extra={...})`. Scout possesses no wallet credentials, no private keys, and no transaction signing capabilities.

### 2. Clerk Inspection & Read Path
Located in [`clerk/engine.py`](clerk/engine.py):

Clerk computes the pending backlog dynamically using event projection. Calling `get_queue()` reads the COLD event stream from `tenant_scout` and cross-references it against historical actions recorded in `tenant_clerk`. If a task has no corresponding action event, it appears in the queue. No secondary mutable database tables or caching layers exist. 

When an entity identity is queried in `check_person(name)`, Clerk inspects `tenant_scout` storage. If the record does not exist, Clerk immediately stamps the request as `NOT ON RECORD` and halts all execution.

### 3. Clerk Execution & Base Settlement
Located in [`clerk/engine.py`](clerk/engine.py) and [`shared/base_client.py`](shared/base_client.py):

When opening a task, Clerk writes an `opened` event to its COLD stream, sets a WARM `task` entity, and records active context in HOT state. When skipping, Clerk commits a `skipped` event to COLD storage. 

When executing a ping, Clerk verifies that the target Person has a valid bound wallet address. If confirmed by the human operator, Clerk broadcasts a transaction to Base Mainnet using `execute_base_ping()` and writes a `pinged` event containing the verified transaction hash. If operator confirmation is missing or prerequisites fail, Clerk writes a `blocked` event with the specific reason. Clerk never simulates or fabricates transaction hashes.

---

## Tiered Memory Architecture

OnRecord maps directly to the five enforced tiers of Sibyl Memory:

| Memory Tier | Active Tenant | Assigned Role | Architectural Purpose |
|---|---|---|---|
| **WARM** | `tenant_scout` | Scout | Canonical storage for `Person` and `Ask` entities |
| **COLD** | `tenant_scout` | Scout | Append-only event journal recording `filed` handoffs |
| **WARM** | `tenant_clerk` | Clerk | Canonical storage for processed `Task` records |
| **COLD** | `tenant_clerk` | Clerk | Action journal recording `opened`, `skipped`, `pinged`, and `blocked` events |
| **HOT** | `tenant_clerk` | Clerk | Ephemeral execution state tracking the currently inspected task |
| **REFERENCE** | `tenant_desk` | Operator | Storage for the system `Charter` and operator runtime `Scene` sources |

---

## Base Mainnet Settlement

All onchain activity occurs on Base Mainnet under Chain ID `8453` using public JSON-RPC infrastructure. Bound addresses originate strictly from operator-specified wallet sources (`wallet:0x...`). Repository-only sources are assigned an empty bound string and cannot receive onchain transactions.

Clerk strictly enforces human-in-the-loop governance. Every transaction requires an explicit confirmation check from the operator before broadcast. If the signing key is absent or confirmation is withheld, Clerk logs a blocked notice and preserves the system state.

---

## Zero Hardcoded Data Guarantee

The platform ships with an empty Scene template (`sources: []`). No preloaded user personas, sample repository constants, or placeholder wallet addresses exist anywhere in the application defaults. All identifiers (`ask_<hash>`, `task_<hash>`) are derived dynamically at runtime from operator inputs. An empty Scene results in zero Scout filings, which produces a completely empty queue.

---

## How Sibyl Memory Made This Possible

OnRecord uses the official `sibyl-memory-client` as its only operational state store. Scout writes `Person` and `Ask` entities plus a `filed` cold-journal event to `tenant_scout`; Clerk reconstructs its queue by reading those persisted events and verifies entities from the same tenant. Clerk actions live in `tenant_clerk`, while the operator Scene and Charter live in `tenant_desk` reference storage. There is no hidden queue, fixture database, vector cache, or fallback repository. Wiping `tenant_scout` therefore removes the queue and changes prior identities to `NOT ON RECORD`.

## Source Integrations

Scout reads only the exact sources saved by the operator. `repo:owner/name` and `repo:owner/name#123` use the GitHub API and never substitute another repository. `wallet:0x...@8453` queries recent Base Mainnet ERC-20 `Transfer` logs through `BASE_RPC_URL` (default `https://mainnet.base.org`); `BASE_SCAN_BLOCKS` tunes the recent block window. If a source cannot be queried or returns no evidence, Scout reports the error and files nothing.

## Base Integration

Base is a partner stack, not a source-of-truth replacement: Base RPC supplies verifiable wallet activity, and the browser wallet or optional server signer performs the operator-confirmed ping. Every recorded ping is checked against Base chain ID `8453`, the bound recipient, task calldata, and a successful receipt before Clerk writes the transaction hash to Sibyl Memory.

## Partner Stack

- **Sibyl Memory:** durable, partitioned state and cold-journal handoffs.
- **Base:** Mainnet RPC and operator-confirmed onchain settlement.
- **GitHub:** live repository issue/ask discovery from an operator-supplied repository.

## Quickstart Guide

### Live Judge Demo

The isolated public judge instance is available at [onrecord-judge.fly.dev](https://onrecord-judge.fly.dev/desk). It starts with an empty database so judges can save a public Scene, run Scout, retrieve records, delete memory, restore it, and optionally sign a Base transaction with their own browser wallet. The private operator deployment is separate.

### 1. Launch the Server
Execute the application server using Uvicorn:
```bash
uvicorn server:app --port 8000
```
Navigate to `http://localhost:8000/desk` to open the operational desk.

Mutation endpoints require the `ONRECORD_ADMIN_TOKEN` environment variable and a
`Bearer` token in the request. Set it before launching:
```bash
export ONRECORD_ADMIN_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
```
The desk prompts for this token when an operator performs a mutation. Never send
private keys through the API; the server signer uses `BASE_PRIVATE_KEY` from its
environment, while browser-wallet hashes are verified against Base before being
recorded.

For a different Base RPC or a larger recent-activity window, configure `BASE_RPC_URL` and `BASE_SCAN_BLOCKS`.

For a hosted instance containing anything other than deliberately public demo data, set `ONRECORD_PROTECT_READS=true`. This requires the same bearer token for Scene, queue, identity, task, and journal reads. A public judge instance may leave it false only when its database contains public demo records and no operator or customer data.

## Public Judge Instance and Base Proof

Run a separate, clean demo deployment with `ONRECORD_JUDGE_MODE=true` and public demo data only. In this mode judges can save a public Scene, run Scout, retrieve entities, execute the delete-memory proof, and restore the snapshot without an operator token. The instance still rejects bind, skip, and server-signed actions. For the optional Base proof, judges connect their own wallet, sign the task transaction in-browser, and verify the resulting hash on Basescan. Keep the operator deployment separate with `ONRECORD_PROTECT_READS=true` and `ONRECORD_JUDGE_MODE=false`.

### 2. Operator Workflow
1. Configure Sources: In the top Scene bar, enter the GitHub repository (e.g. `owner/repo`) and Base wallet address to monitor, then click **Save Scene**.
2. Run Scout: Click **Run Scout** to discover inbound work. Scout parses incoming activity and commits structured files into `tenant_scout`.
3. Inspect Queue: Newly filed tasks populate the Queue column. Click any task card to open the Clerk inspector panel.
4. Verify Entities: Enter an identity in the top-right verifier and click **Check**. If the entity was never filed by Scout, Clerk stamps `NOT ON RECORD`.
5. Execute Actions: Choose to open, skip, or confirm an onchain Base ping for wallet-bound contributors.

---

## Memory Verification & The Delete Test

The repository provides automated verification scripts demonstrating load-bearing memory properties across separate operating system processes.

### Multi-Process Recall Verification
Run the recall test script to observe state persistence across distinct process lifecycles:
```bash
python scripts/recall.py --name "Desk" --sources repo:fastapi/fastapi wallet:0x000000000000000000000000000000000000dEaD@8453
```
Session A boots under a specific process ID, files records into memory, and terminates. Session B starts under a completely new process ID with zero in-memory variables, reconstructs the task backlog directly from `data/onrecord.db`, and validates entity verification.

### Automated Judge Proof Script
Execute the unified proof runner:
```bash
python scripts/proof.py
```
PowerShell users can run:
```powershell
pwsh -File scripts/proof.ps1
```

### The Delete Test
The delete test demonstrates that memory is strictly load-bearing:
1. When `tenant_scout` rows are wiped from `data/onrecord.db`, the projected backlog immediately drops to zero.
2. Previously filed entity names queried against Clerk return `NOT ON RECORD`.
3. The underlying GitHub and blockchain endpoints continue to exist, but the desk's operational state cleanly disappears.

## Prior Work

OnRecord is an original implementation for this submission. It does not claim prior Sibyl hackathon placement, an inherited product, or a pre-existing partner integration. The repository history contains the implementation work; the runtime Scene remains empty until an operator supplies sources.

---

## Automated Test Suite

Run the full pytest integration suite:
```bash
python -m pytest tests/
```
The test suite validates source format regular expressions, verifies zero-write behavior on empty scenes, tests cross-session recall, exercises HTTP authorization boundaries, and executes the tenant deletion proof.

Run the dependency audit before release:
```bash
python -m pip install pip-audit
python -m pip_audit -r requirements.txt --progress-spinner off
```
This check needs access to the Python vulnerability service. A network timeout is an environment failure, not a clean audit result.

---

## Contributor

**Datwebguy**
GitHub: [https://github.com/Datwebguy](https://github.com/Datwebguy)

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for complete terms.
