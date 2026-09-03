# Memory

Durable facts only. Not a chat log.

## Decision

Name: OnRecord
Shape: Build 3. Two tenants. One operator. One action path.
Scene: empty until the operator saves sources.

## Tenants

- tenant_scout
- tenant_clerk
- tenant_desk

## Charter (REFERENCE tenant_desk / charter)

{
  "scout": "file only",
  "clerk": "act only on filed tasks",
  "ping": "only to a Person with a bound address"
}

Charter is policy. It is not a source list.

## Scene (REFERENCE tenant_desk / scene)

{
  "name": "",
  "sources": [],
  "updated": ""
}

Operator overwrites this at runtime. Repo copy stays empty.

## Bodies (shapes, not rows)

Do not insert these as seed data.

Person (Scout WARM, category person, name = generated or handle from source)
{
  "name": "",
  "handle": "",
  "bound": "",
  "last_ask": ""
}

Ask (Scout WARM, category ask, name = generated ask id)
{
  "id": "",
  "from": "",
  "text": "",
  "source": "",
  "filed_at": ""
}

Task (Clerk WARM, category task, name = generated task id)
{
  "id": "",
  "from_ask": "",
  "person": "",
  "allowed": ["skip", "reply", "ping"],
  "status": "open"
}

bound is an 0x address only if the operator’s Scene or the source supplied one.
Empty bound → ping button stays disabled.

## Facts to update as work happens

- Scene filled by operator: Implemented via tenant_desk REFERENCE (`scene`), validated against regex.
- Scout write path: Implemented via `scout/engine.py` (WARM person/ask + COLD filed event).
- Clerk read path: Implemented via `clerk/engine.py` (dynamic queue projection from COLD + NOT ON RECORD on miss).
- UI: Implemented via `static/` 3-column desk (Scout journal, Queue, Clerk actions + verifier).
- Base ping: Implemented via `shared/base_client.py` on Base Mainnet (8453) with operator confirmation and blocked logging.
