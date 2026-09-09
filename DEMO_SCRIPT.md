# Demo package — OnRecord

## Logline

OnRecord lets operators act only on work that durable memory can prove.

## Judge retell

“OnRecord deletes its memory, loses the queue, and proves the work was never just hidden state.”

## Primary wedge

Configure one public GitHub source → Scout files live work → a fresh Clerk session recalls it → Delete Test removes it → Restore brings it back.

This is the primary video flow because it directly proves Sibyl Memory is load-bearing. Base settlement is secondary and should only appear if a genuine transaction is ready.

## Reality check

### Live

- Public judge app: <https://onrecord-judge.fly.dev/desk>
- Judge mode allows public Scene save, Scout, Delete Test, and Restore Memory.
- The judge database starts intentionally empty.
- GitHub reads the exact repository supplied by the operator.
- Sibyl Memory persists Scene, Person, Ask, Task, and journal state.
- Delete Test wipes Scout memory and removes the queue.
- Restore Memory recovers the snapshot.

### Live but only show if prepared

- Base Mainnet browser-wallet flow.
- Network: Base Mainnet, Chain ID `8453`.
- A real transaction must be executed and visible on Basescan.
- Never show a fabricated hash or mocked transaction.

### Mocked or test-only

- Automated tests mock external Base verification.
- Do not present mocked test output as a live Base transaction.
- Do not expose the private operator app, bearer token, local database, or private wallet.

## 2:20 shoot script

Use a visible UTC timestamp and commit overlay throughout:

`OnRecord · commit 7d0b3e1 · 2026-09-08`

| Time | On screen | Burn-in caption | Voice | Action | If this breaks |
|---|---|---|---|---|---|
| 0:00–0:12 | Public judge desk, empty Scene and Queue | `Incoming work should not become action without a record.` | “When an agent receives work, the dangerous part is not discovery. It is acting on something nobody can prove was recorded.” | Start on the live judge desk. Keep the empty queue visible. | Use a clean backup recording of the same public judge URL. |
| 0:12–0:25 | Scene inputs | `ONE SOURCE. ONE RECORD.` | “OnRecord gives one operator a simple rule: Scout files evidence, and Clerk only acts on what is on record.” | Enter `fastapi/fastapi`. Leave the wallet field empty. Click **Save Scene**. | Use `repo:fastapi/fastapi#16328` if the repository feed is slow. |
| 0:25–0:45 | Scene saved, then Scout button | `SCOUT → SIBYL MEMORY` | “This is a real public GitHub source. OnRecord does not fall back to another repository or invent an issue if the source fails.” | Click **Run Scout**. Wait for the filing count and journal to update. | If no filing appears, show the error honestly. Do not pretend the queue populated. |
| 0:45–1:05 | Scout filings and Queue | `FILED: PERSON + ASK + COLD EVENT` | “Scout has found live repository activity and written structured Person and Ask records into Sibyl Memory. The queue is projected from those persisted events.” | Point to the filing, then the Queue count. Read the visible contributor name and task title. | If there are multiple cards, use the first visible card. |
| 1:05–1:25 | New tab or refreshed judge desk | `FRESH SESSION RECALL` | “Now I’m changing sessions. This browser session has no application memory from the previous step.” | Open a fresh tab to the judge URL, or refresh the desk. | If the fresh tab is slow, refresh the same desk and show the new page load. |
| 1:25–1:42 | Queue restored, Clerk card selected | `CLERK RECONSTRUCTS FROM MEMORY` | “The queue is back because Clerk reconstructed it from Sibyl’s persisted event stream.” | Click the same queue card. Show the Clerk panel and memory file view. | Scroll only the Queue or Clerk panel if needed. |
| 1:42–1:53 | Verifier with recorded person | `ON RECORD` | “The filed identity is verified as ON RECORD.” | Enter the visible person name in **Verify handle** and click **Check**. | Use the visible handle exactly as shown. |
| 1:53–2:00 | Delete Test button | `ONE CLICK: DELETE MEMORY` | “Now the proof: I delete Scout memory.” | Click **Delete Test**, confirm the browser prompt, and wait for the success toast. | Click the button again if the prompt was missed. |
| 2:00–2:08 | Empty Queue | `QUEUE 0` | “The queue is now zero.” | Hold the empty Queue and Delete Test result for three seconds. | Reload once if the page does not refresh. |
| 2:08–2:15 | Verifier with same person | `NOT ON RECORD` | “The source still exists on GitHub. But the operational record is gone, so the same person is now NOT ON RECORD.” | Run the same identity check again. | Scroll the Clerk panel to the verifier if needed. |
| 2:15–2:20 | Restore result | `MEMORY RESTORED` | “Restore brings the recorded state back. That is OnRecord: no durable record, no action.” | Click **Restore Memory** and hold the result. | End on the Delete Test proof if restore takes too long. |

### Spoken script

“When an agent receives work, the dangerous part is not discovery. It is acting on something nobody can prove was recorded.

OnRecord gives one operator a simple rule: Scout files evidence, and Clerk only acts on what is on record.

This is a real public GitHub source. OnRecord does not fall back to another repository or invent an issue if the source fails.

Scout has found live repository activity and written structured Person and Ask records into Sibyl Memory. The queue is projected from those persisted events.

Now I’m changing sessions. This browser session has no application memory from the previous step.

The queue is back because Clerk reconstructed it from Sibyl’s persisted event stream.

The filed identity is verified as ON RECORD.

Now the proof: I delete Scout memory.

The queue is now zero.

The source still exists on GitHub. But the operational record is gone, so the same person is now NOT ON RECORD.

Restore brings the recorded state back. That is OnRecord: no durable record, no action.”

## 45-second cut

1. Open the public judge desk.
2. Enter `fastapi/fastapi`.
3. Click **Save Scene**.
4. Click **Run Scout**.
5. Show a filed card and Queue count.
6. Refresh in a fresh tab.
7. Show the queue returning.
8. Click **Delete Test**.
9. Hold `Queue 0`.
10. Verify the same person as `NOT ON RECORD`.

Voiceover:

“OnRecord prevents agents from acting on work they cannot prove was recorded.

I give Scout one public GitHub source and run it. Scout writes the Person, Ask, and filed event into Sibyl Memory.

Now I open a fresh session. Clerk reconstructs the queue from persisted memory.

I delete Scout memory. The queue immediately drops to zero, and the same identity becomes NOT ON RECORD.

The source still exists. The record does not. That is the proof that Sibyl Memory is load-bearing.”

## 12-second hook

“Watch me delete the memory. The GitHub source still exists, but the queue becomes zero and the person becomes NOT ON RECORD. OnRecord acts only on what memory can prove.”

## Proof shot list

Freeze each shot for at least three seconds:

1. Public URL: <https://onrecord-judge.fly.dev/desk>
2. Scene saved with `fastapi/fastapi`.
3. Scout filing showing the Person name, Ask title, and Queue count greater than zero.
4. Fresh session showing the same Queue count and reconstructed task.
5. Before deletion: verifier result `ON RECORD`.
6. Delete result: memory-wiped toast and Queue `0`.
7. After deletion: same identity showing `NOT ON RECORD`.
8. Restore result: `Memory restored`.

Keep this overlay visible:

`7d0b3e1`

## Pre-flight

- Open the judge URL in a clean browser profile.
- Confirm `/api/status` reports `judge_mode: true`.
- Confirm Scene is empty before recording.
- Use only the public source `fastapi/fastapi`.
- Have a second fresh tab ready.
- Set browser zoom to 125%.
- Use a large visible cursor.
- Enable Do Not Disturb.
- Hide bookmarks, personal tabs, email, wallet balances, and local paths.
- Burn a UTC timestamp and commit hash into the recording.
- Do not enter an admin token.
- Do not show the private operator URL.
- Do not include a wallet unless a real Base transaction is prepared.
- Record continuously from Scene save through deletion and restore.

## Failure plan

If GitHub or Scout fails, say:

> “The source is unavailable, so OnRecord refuses to create a filing. That is the safety behavior.”

Use a pre-captured successful judge recording. Do not fabricate a queue.

If the judge API is temporarily down, say:

> “I’m switching to the prepared continuous recording of the same public judge flow. The important proof is the persisted recall and deletion result.”

If the wallet prompt appears or a transaction fails, say:

> “The Base action is optional. I’m not claiming an onchain result without a successful receipt, so I’m ending on the memory proof.”

Backup clip:

- Successful Scout filing.
- Fresh-session queue recall.
- Delete Test showing Queue `0`.
- Same identity showing `NOT ON RECORD`.

## X / submission caption

### Primary memory-only cut

OnRecord lets operators act only on work durable memory can prove.

Proof: live Sibyl Memory recall and delete test on the public judge instance: <https://onrecord-judge.fly.dev/desk>

Built for the Sibyl Labs Hackathon. @sibylcap

### If a genuine Base transaction is added

OnRecord lets operators act only on work durable memory can prove.

Proof: Sibyl Memory recall/delete plus a real Base Mainnet transaction, Chain ID 8453: <https://onrecord-judge.fly.dev/desk>

Add the official Base handle only if the executed Base action appears in the video.

## Judge FAQ

### What happens if Sibyl Memory is deleted?

The Scout queue disappears, and previously filed identities return `NOT ON RECORD`.

### Is the queue stored in a hidden application database?

No. Clerk reconstructs the queue from Sibyl Memory events and reads entities from the persisted Scout tenant.

### Does Scout use a fallback repository?

No. It reads only the exact source supplied in the Scene. If the source fails, it files nothing and reports an error.

### Is the Base transaction real?

The Base path is real code, but it should only be claimed when a successful browser-wallet transaction and Basescan receipt are visible. The primary demo does not depend on Base settlement.

### Can judges use the platform without an operator token?

Yes. The isolated judge deployment runs in judge mode and allows safe demo operations. The private operator deployment remains protected.

## Contest adapter

This demo is designed for the Sibyl Labs Hackathon:

- **Memory gate:** fresh-session recall is shown in one continuous segment.
- **Critical-path calls:** the README links Scout writes in `scout/engine.py` and Clerk reads in `clerk/engine.py`.
- **Deletion test:** the demo wipes Scout memory and shows Queue `0` plus `NOT ON RECORD`.
- **Technical execution:** the public judge instance can be run repeatedly.
- **Pitch and presentation:** the story fits inside the required 2–5 minute window.
- **Base multiplier:** do not claim it unless a real Base Mainnet action is executed and shown.
- **Submission:** public MIT repository, README, real commit history, 2–5 minute demo, and two public posts.

Official rules: <https://hack.sibyllabs.org/rules>

## Cut list

Do not show:

- Private operator dashboard.
- Bearer tokens.
- `.env` files.
- SQLite files or local Windows paths.
- Seed phrases or private keys.
- Wallet rejection or insufficient-gas errors.
- Mocked transaction hashes.
- Test output presented as production evidence.
- Landing-page architecture tour.
- Pitch deck.
- Extra dashboards or unrelated features.
- GitHub as the opening shot.
- Testnet activity while claiming Base Mainnet.
- Lookalike tokens or unofficial assets.
- A second persona or complicated multi-user story.

## PowerShell proof recording

Record these commands one at a time. Keep the PowerShell window visible and wait for each command to finish before typing the next one.

### Setup — create a clean local proof database

Command:

```powershell
python -c "from shared.db import init_desk,get_desk_client; from shared.models import utc_now_iso; db='data/demo-proof-02.db'; init_desk(db); get_desk_client(db).set_reference('scene', {'name':'Judge Proof','sources':['repo:fastapi/fastapi'],'updated':utc_now_iso()}); print('Scene initialized')"
```

Say:

> “I’m creating a clean local proof database and saving one public source. This does not touch the deployed judge instance.”

Show:

```text
Scene initialized
```

### Session A — Scout writes memory

Command:

```powershell
python scripts/recall.py --db data/demo-proof-02.db --internal-session A
```

Say:

> “This is Session A. Scout is running in its own process and writing the live source results into Sibyl Memory.”

Show:

- The Session A banner.
- The process ID.
- The timestamp.
- `Scout sync completed`.
- Filed task and person lines.

Close with:

> “Session A terminates now. The next command will start a different process.”

### Session B — Clerk recalls memory

Command:

```powershell
python scripts/recall.py --db data/demo-proof-02.db --internal-session B
```

Say:

> “This is Session B. It starts with a new process ID and no Session A variables. Clerk is reconstructing the queue directly from persisted Sibyl Memory.”

Show:

- A different process ID.
- `Clerk projected 10 pending tasks directly from Sibyl Memory` or the current count.
- `NOT_ON_RECORD` for the unfiled identity.
- The filed task details.

Close with:

> “The fresh process recovered the queue, while an identity that was never filed was rejected.”

### Delete Test — remove the memory layer

Command:

```powershell
python scripts/recall.py --db data/demo-proof-02.db --internal-session DELETE
```

Say:

> “Now I’m deleting the Scout memory partition. The source still exists, but the operational record should disappear.”

Show:

- The Delete Test banner.
- The number of deleted rows.
- Queue length `0`.
- The previously filed person returning `NOT ON RECORD`.
- `Delete Test Passed`.

Close with:

> “That is the Sibyl invariant: delete the memory, and the queue disappears. The desk is the files.”

### Terminal proof caption

Keep this caption on screen:

`SESSION A WRITE → SESSION B RECALL → DELETE → QUEUE 0 / NOT ON RECORD`

## Appendix

### Secondary features

- Base wallet activity ingestion through public Base RPC.
- Browser-wallet transaction confirmation.
- Operator-only task open and skip actions.
- Bound wallet management.
- Scout and Clerk event journals.
- Public and protected deployment modes.
- Restore-from-snapshot memory recovery.

### Stack

- FastAPI
- Sibyl Memory Client
- SQLite-backed persistent storage
- GitHub API
- Base Mainnet JSON-RPC
- Browser wallet integration
- Fly.io deployment

### Roadmap

- Add a stable public demo fixture based only on real public source evidence.
- Add a successful recorded Base transaction to the submission cut if the wallet and gas are prepared.
- Complete `pip-audit` when the vulnerability-service network lookup is available.
- Publish the required demo and build-log posts.

## Recording decision

Record the primary memory-only cut first. It is the most reliable, directly satisfies the Sibyl gate, and does not depend on a live wallet transaction.
