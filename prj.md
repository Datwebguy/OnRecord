# OnRecord

Scout files. Clerk only acts on what is on record.

You
  │  set Scene at runtime, confirm the one hard action
  ▼
Scout          Clerk
read + file    act only on files
tenant_scout   tenant_clerk
     │              ▲
     └── handoff ───┘
         COLD event
         no row = no action

REFERENCE (tenant_desk): Charter, Scene
Scene starts empty. Operator fills it. Nothing in the repo is a source.
Base wallet: Clerk may propose. You confirm. Scout never signs.

## What this is

A desk anyone can run. Two roles. One operator. Work only moves as files.

- Scout reads only sources the current operator saved in Scene. Writes Person, Repo, Ask. Writes COLD filed. Never pings. Never spends.
- Clerk opens only what Scout filed. Missing file → NOT ON RECORD. One move: skip, reply text, or propose a Base ping.
- Operator owns Scene. Confirms pings. Kills the process and starts a new one for recall.

## Non-negotiables

- Product name is OnRecord. Repo folder is onrecord.
- Do not start with two LLM personas chatting.
- The structure is the files. The models only sit on top.
- Do not clone SIBYL or Janus by name.
- Do not add a SpendGuard.
- Do not snapshot a portfolio.
- Do not mix other builds into this repo.
- Product copy must not use the word hackathon.
- Entity names and categories: no hyphens. Unique per (tenant_id, category, name).
- No hardcoded people, asks, repos, wallets, Dune queries, or dates in runtime data.
- scene.json ships empty. sources is [].
- Do not add scene.example.json.
- Demo fixtures, if any, are created at runtime from operator input and are wipeable.

## Build order (strict)

1. Charter template in repo. Scene empty.
2. First-run: operator names the desk and pastes sources. That write is Scene.
3. Scout write path: set_entity + write_event.
4. Clerk read path: no file, no act.
5. Then UI.
6. Then one Base ping.

## Memory

| Store | Tenant | Who writes | Contents |
|---|---|---|---|
| WARM | tenant_scout | Scout | Person, Repo, Ask |
| COLD | tenant_scout | Scout | seen, quoted, filed |
| WARM | tenant_clerk | Clerk | Task |
| COLD | tenant_clerk | Clerk | opened, skipped, pinged, blocked |
| REFERENCE | tenant_desk | operator | Charter, Scene |
| HOT | tenant_clerk | Clerk | open_task |

Same sqlite file. Three tenants. Isolation is the product.

The desk process may open all three tenants. That is routing, not a shared brain.

- Scout writes only tenant_scout.
- Clerk writes only tenant_clerk.
- Clerk may read tenant_scout to open a filed ask. Miss → stop.
- Neither role writes the other role's WARM or COLD.

## Scene

Runtime only. Shape:

{
  "name": "",
  "sources": [],
  "updated": ""
}

Allowed source strings, validated when the operator saves Scene, never prefilled:

- repo:owner/name
- repo:owner/name#n
- wallet:0x<40hex>@8453
- dune:address:0x<40hex>

Empty sources → Scout files nothing → queue empty. That is correct.

## Handoff

COLD write by Scout, then COLD read by Clerk.

Scout acted: filed <ask_id> person=<name> -> <task_id>
Clerk acted: opened <task_id>
Clerk acted: pinged <task_id> tx=<hash>   or   skipped | blocked

No filed row. Clerk returns NOT ON RECORD and does not act.

Ask ids, person names, and task ids are generated at runtime from what Scout actually saw. Do not bake sample ids into code.

## Delete test

| Cut | What dies |
|---|---|
| Scout tenant | Queue dries up. Clerk has nothing to open. |
| Clerk tenant | Action history gone. Same ask can be pinged twice. |
| Both | Live sources still exist on GitHub / chain. OnRecord does not. |

## Definition of done

- First run with empty Scene shows an empty queue and a form to add sources.
- Operator saves at least one real source they choose. No source is supplied by the repo.
- Session A: Scout files a Person + Ask + filed event from that Scene. Process stops.
- Session B: new process. Clerk opens that task from memory. An unfiled name stamps NOT ON RECORD. Filed Person with bound address can be pinged after confirm.
- One Base result recorded as Clerk COLD. Scout never signs.
- README points at the Scout write and the Clerk read_events + get_entity calls.
