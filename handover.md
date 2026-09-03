# Handover

Empty folder except these six files. Build OnRecord here.

## Repo layout

onrecord/
  README.md
  prj.md
  hackathon.md
  product.md
  resources.md
  memory.md
  handover.md
  charter.json
  scene.json
  scene.schema.json
  scout/
  clerk/
  shared/
  demo/
  data/.gitkeep
  .gitignore

License MIT.

.gitignore:
data/
scene.json
.env
.env.local

## Step 1 — Charter and empty Scene

charter.json:

{
  "scout": "file only",
  "clerk": "act only on filed tasks",
  "ping": "only to a Person with a bound address"
}

scene.json:

{
  "name": "",
  "sources": [],
  "updated": ""
}

scene.schema.json validates types only. No example sources inside it.

On first run, operator also set_reference charter and scene on tenant_desk.
If Scene sources is still [], Scout does not invent work.

## Step 2 — Scout write path

scout/ reads Scene.
If sources is empty, exit cleanly.
For each new ask discovered from those sources:
- set_entity("person", name, body)
- set_entity("ask", ask_id, body)
- write_event(acted=[filed line], extra={...})

Ids are generated. No sample ids in code.
Scout has no wallet. Scout does not write tenant_clerk.

## Step 3 — Clerk read path (no file, no act)

clerk/ read path only:

- read_events on tenant_scout looking for acted that starts with "filed"
- read_events on tenant_clerk looking for opened / skipped / pinged / blocked
- queue = filed with no opened
- get_entity("ask", id) and get_entity("person", name) on tenant_scout
- miss → NOT ON RECORD
- hit → show Task proposal
- do not set_entity
- do not write_event
- do not ping
- do not create files

## Step 4 — UI

Three columns from product.md.
First-run Scene form.
Queue is computed from COLD, not from model memory.
No placeholder cards.

## Step 5 — One Base ping

Only after read path and UI work.
Clerk write path:

- write_event opened
- set_entity task
- set_state open_task
- wait for operator confirm
- send one Base ping to Person.bound
- write_event pinged with tx or blocked with error

Unknown name → NOT ON RECORD, no tx.
Empty bound → button disabled, no tx.

## Fresh session

New process. No chat transcript. Clerk loads tenants from Sibyl Memory.

## Stop

When empty-Scene empty-queue, operator-filled Scene, Session A file, Session B recall, one ping, and delete-Scout-empty-queue all work, stop.
Update memory.md.
Do not add a second scene kind. Do not add a second agent voice.
