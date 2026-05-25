# Roadmap

## Phase 0: Product framing

Goal:
- lock the product structure before implementation

Deliverables:
- overview
- spec
- issue breakdown

## Phase 0.5: App shell ✓ (Issue #2, 2026-05-25)

Deliverables:
- Astro 5 + vanilla TypeScript app shell
- `Library` and `Book` pages with nav
- `localforage` (IndexedDB) persistence layer
- seed data survives reloads
- `src/lib/types.ts` — domain model (Asset / Book / Page / Placement)
- `src/lib/db.ts` — loadAssets / saveAssets / loadBook / saveBook / seedLibrary
- `src/lib/library.ts` — renderAssetGrid helper

## Phase 1: Core collection MVP

Goal:
- prove the library + book split

Target:
- user can import an image
- turn it into a sticker-like asset
- place it on a themed page
- move it around
- peel it off
- export the result

## Phase 2: Stamp path

Goal:
- support travel stamp style collection

Target:
- stamp capture import
- basic background removal
- reverse-from-rubber workflow
- ink recolor

## Phase 3: Theme variety

Goal:
- make page themes meaningfully different

Target:
- sticker book page
- stamp book page
- scrapbook page

## Phase 4: Collection storytelling

Goal:
- make the book feel personal and worth sharing

Target:
- labels
- page metadata
- page sequences
- short-video export

## Phase 5: Exchange

Goal:
- let collections circulate without central servers

Target:
- QR-based transfer experiments
- ownership metadata
- trust-based "give away" flow
