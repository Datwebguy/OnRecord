# Product

OnRecord is a two-agent desk for incoming work.

Scout reads. Clerk acts only on files. The operator confirms the irreversible step.

Anyone can run it. The operator brings the sources. The product does not.

## Scene

Scene is the allowlist of what Scout may look at.

It is empty until the operator saves it.

Allowed kinds, operator-pasted only:

- repos they actually watch
- wallets they actually watch
- optional Dune address lookup for an address they pasted

Do not invent a marketplace of builders. Do not ship a default watchlist.

## Screen

Three columns. Not two chat toys.

1. Scout — last files written, raw source line
2. Queue — filed tasks with no opened event
3. Clerk — the open task, the Person card, the stamp: ACT / SKIP / NOT ON RECORD

Top or first-run: Scene form. Name the desk. Paste sources. Save.
If sources is empty, show that state. Do not fake a queue.

Bottom: one ping button. Disabled unless Person.bound exists and the operator has confirmed.

## Stamps

- ACT — Person and Ask exist, task opened
- SKIP — operator chose skip, COLD skipped written
- NOT ON RECORD — get_entity missed or no filed event

## What it is not

- Not SIBYL and Janus
- Not Clerk.com
- Not a spend bot
- Not a portfolio
- Not two models talking
- Not a demo seeded with sample people
