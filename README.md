# petit-collection

Turn your own photos, drawings, and stamp captures into collectible pieces, then place them
onto pages that feel like a sticker book, stamp notebook, or scrapbook.

`petit-collection` is planned as a local-first web app for children, collectors, and anyone
who wants the feeling of "I made this collection myself" without buying official goods.

## What it aims to do

- make stickers from your own images
- capture travel stamps and keep them in one place
- arrange pieces onto themed pages
- keep the collection on your device, without mandatory accounts or subscriptions

The emotional target is not "media manager." It is "a book I want to keep opening."

## Planned experience

### Make-believe collecting

You can build a collection from:

- insects
- flowers
- ships
- original characters
- hand-drawn doodles
- travel stamps

### Book-first interaction

The app should feel like:

- a sticker album
- a stamp notebook
- a scrapbook
- a moodboard binder

not like a spreadsheet or a cloud dashboard.

### Local-first ownership

The collection belongs to the device unless the user explicitly exports it.
No subscription and no mandatory server are part of the product identity.

## Product shape

The app is planned around two surfaces:

1. `Library`
   - browse owned assets
   - inspect metadata
   - search, sort, and filter

2. `Book`
   - place assets onto pages
   - flip through pages
   - rearrange compositions
   - enjoy the collection as an object

The HyperCard inspiration applies to the `Book` side, not to the raw asset library.
Assets are data-rich. Pages are behavior-rich.

## Current status

This repository is still in pre-implementation planning.
Some important capabilities are blocked by growth in related projects:

- a not-yet-separated perspective-correction foundation
- `mypace` for rotation/placement know-how
- exchange design work that may later touch `Nostr`

That is exactly why the project now keeps a clearer issue backlog with blocker notes.

## Docs

- `docs/overview.md` — product intent and boundaries
- `docs/spec.md` — domain model and MVP contract
- `docs/roadmap.md` — development phases
- `docs/research-notes.md` — competitor notes and dependency observations
- `docs/issue-backlog.md` — issue drafts, priorities, and blocker mapping
- `CLAUDE.md` — AI-facing development guide
