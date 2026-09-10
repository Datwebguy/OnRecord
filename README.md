<div align="center">

# OnRecord

**Durable memory between AI-agent discovery and action.**

Scout files evidence. Clerk verifies it. No record means no action.

[![Network: Base Mainnet](https://img.shields.io/badge/Network-Base%20Mainnet%20%288453%29-0052FF?style=for-the-badge&logo=coinbase&logoColor=white)](https://base.org/)
[![Memory: Sibyl](https://img.shields.io/badge/Memory-Sibyl-8A2BE2?style=for-the-badge)](https://sibyllabs.ai/)
[![License: MIT](https://img.shields.io/badge/License-MIT-C81E1E?style=for-the-badge)](LICENSE)

<br />

[Open the public judge desk](https://onrecord-judge.fly.dev/desk)

</div>

## What OnRecord does

OnRecord is an operational desk for agent systems that receive work from public sources and may later take consequential action. It separates discovery from execution with two explicit roles:

- **Scout** reads an operator-configured GitHub repository or Base wallet activity and files structured `Person` and `Ask` records.
- **Clerk** reconstructs its queue from persisted Sibyl Memory events, verifies identities, and records every decision.
- **The operator** remains the final authority for any irreversible action, including an optional Base transaction.

The core safety rule is deliberately simple: an entity that was not filed is **NOT ON RECORD** and cannot become an operational task.

## Why the memory layer matters

Sibyl Memory is load-bearing, not decorative storage. OnRecord uses the official `sibyl-memory-client` with a SQLite-backed memory store at `data/onrecord.db`.

| Tenant | Role | Purpose |
| --- | --- | --- |
| `tenant_scout` | Scout | `Person` and `Ask` entities plus the append-only `filed` journal |
| `tenant_clerk` | Clerk | `opened`, `skipped`, `blocked`, and `pinged` action events |
| `tenant_desk` | Operator | Charter and active Scene configuration |

Clerk does not read a hidden queue or a second task database. It projects pending work from Scout's persisted events. Delete `tenant_scout`, and the queue disappears; the same identity becomes `NOT ON RECORD`. Restore the snapshot, and the recorded state returns.

The main integration points are:

- [`scout/engine.py`](scout/engine.py) — source ingestion and Sibyl write path
- [`clerk/engine.py`](clerk/engine.py) — queue projection, verification, and action journal
- [`shared/db.py`](shared/db.py) — tenant-scoped memory access and deletion proof
- [`shared/base_client.py`](shared/base_client.py) — Base transaction execution and receipt verification

## Live judge deployment

The public judge desk is available at:

**https://onrecord-judge.fly.dev/desk**

It is a deliberately separate demo deployment. Judges can save a public Scene, run Scout against a public GitHub repository, inspect the queue, verify a recorded or unfiled identity, delete Scout memory, and restore the snapshot. The deployment is intended for public demo data only; it is not the private operator environment.

The optional Base path requires the judge's own browser wallet and an explicit confirmation. The demo does not use a server-held private key, and no transaction is implied by the existence of a task.

## Sources and partner stack

OnRecord accepts only explicit source formats:

- `repo:owner/name` — recent public GitHub issues and pull requests
- `repo:owner/name#123` — one public GitHub issue or pull request
- `wallet:0x<40-hex-address>@8453` — recent Base Mainnet ERC-20 transfer activity through JSON-RPC

If a source cannot be queried or returns no evidence, Scout reports the error and files nothing. It does not substitute another repository or invent an event.

The partner stack is intentionally small:

- **Sibyl Memory** — durable, partitioned agent state and append-only handoff events
- **Base Mainnet** — optional, operator-confirmed settlement on chain `8453`
- **GitHub** — live public repository discovery from the operator's exact source

## Run locally

Requirements: Python 3.11+, a virtual environment, and network access for live GitHub/Base sources.

### PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn server:app --port 8000
```

Open [http://localhost:8000/desk](http://localhost:8000/desk).

For a protected operator deployment, configure an admin token before starting the server:

```powershell
$env:ONRECORD_ADMIN_TOKEN = python -c "import secrets; print(secrets.token_urlsafe(32))"
```

For hosted instances containing anything other than public demo records, also set `ONRECORD_PROTECT_READS=true`. Never commit `.env`, private keys, bearer tokens, or customer data.

## Verify the memory invariant

Run the multi-process proof from the repository root:

```powershell
python scripts/recall.py --db data/demo-proof-01.db --name "Judge Proof" --sources repo:fastapi/fastapi
```

The script demonstrates separate Scout and Clerk operating-system processes, cross-session recall, an unfiled identity returning `NOT_ON_RECORD`, and a blocked Base action when no wallet is bound.

Run the automated suite and dependency audit:

```powershell
python -m pytest tests/
python -m pip install pip-audit
python -m pip_audit -r requirements.txt --vulnerability-service osv --progress-spinner off --timeout 15
```

## Security posture

- The default Scene is empty; the application ships without preloaded customer identities or wallets.
- Scout has no signing key and cannot broadcast transactions.
- Clerk requires explicit operator confirmation before a Base ping.
- Browser-supplied transaction hashes are verified against Base before being written to memory.
- Mutating API endpoints require a bearer token unless the isolated public judge mode explicitly permits the demo actions.
- The public judge deployment must contain public demo data only. Use protected reads and a separate deployment for private data.

## Project layout

```text
scout/       Source ingestion and filing agent
clerk/       Queue projection, verification, and actions
shared/      Models, memory access, and Base client
scripts/     Recall, proof, and verification commands
tests/       Integration and authorization tests
static/      Desk frontend assets
video/       Remotion demo project
```

## Status and scope

OnRecord is an original MIT-licensed implementation. The public judge flow is designed to make the Sibyl Memory dependency observable: write records, start fresh, recall them, delete them, observe `NOT ON RECORD`, and restore them.

The Base integration is optional and human-controlled. The application does not claim that a transaction occurred unless it can verify a successful Base receipt.

## License

OnRecord is released under the [MIT License](LICENSE).

## Author

[Datwebguy](https://github.com/Datwebguy)
