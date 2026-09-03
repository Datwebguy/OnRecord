# Resources

## Sibyl Memory

pip install sibyl-memory-client

from sibyl_memory_client import MemoryClient

scout = MemoryClient.local("data/onrecord.db", tenant_id="tenant_scout")
clerk = MemoryClient.local("data/onrecord.db", tenant_id="tenant_clerk")
desk  = MemoryClient.local("data/onrecord.db", tenant_id="tenant_desk")

Same file. Three tenants. Isolation is the product.

WARM: set_entity(category, name, body) / get_entity(category, name)
COLD: write_event(acted=..., extra=...) / read_events(...)
HOT:  set_state(key, body) / get_state(key)
REFERENCE: set_reference(key, body) / get_reference(key)

Docs: https://docs.sibyllabs.org/memory/concepts
SDK: https://github.com/Sibyl-Labs/Sibyl-Memory

Categories: person, repo, ask, task
Reference keys: charter, scene
HOT key: open_task

Identifiers: no hyphens in tenant_id, category, or name.

## Scene schema (types only, no sources)

{
  "name": "string",
  "sources": ["string"],
  "updated": "string"
}

Source pattern, checked only on save:

^(repo:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(#[0-9]+)?|wallet:0x[a-fA-F0-9]{40}(@[0-9]+)?|dune:address:0x[a-fA-F0-9]{40})$

.gitignore must include:
data/
scene.json

Do not commit a filled scene.json.
Do not add scene.example.json.

## COLD write mechanics

A COLD write is append-only. write_event inserts a journal row for that tenant.
It does not edit Person or Ask. Those are WARM.

Scout files by:
1. set_entity person
2. set_entity ask
3. write_event(acted=["filed ..."], extra={...})

That third call is the handoff. Clerk looks for filed rows with no matching opened row on tenant_clerk.

## Event sourcing on this desk

- Scout stream = tenant_scout journal
- Clerk stream = tenant_clerk journal
- Task status is projected from Clerk COLD + Task WARM
- If projection and journal disagree, journal wins
- No filed event → no Task → no ping

## Base

One confirmed send to Person.bound after Session A filed that person.
Person.bound comes from Scene or from what Scout read. Never from a constant in source.
Use a tiny Python / viem client against Base.
Record tx hash in Clerk COLD extra.
Scout has no signer.

## Stack

- Python 3.12
- sibyl-memory-client
- FastAPI + one static page for the three columns
- MIT

## Do not pull in

- Clerk.com
- SpendGuard
- Virtuals unless asked later
- A second database for tasks
- Sample users, sample wallets, sample repos
