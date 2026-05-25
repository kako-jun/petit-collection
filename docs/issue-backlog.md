# Issue Backlog

Prepared on 2026-05-25.

This file serves two purposes:

1. draft text for future GitHub issues
2. dependency map showing which work is blocked by other projects

GitHub issues were created on 2026-05-25.
The initial failure came from an invalid `GITHUB_TOKEN` in the shell environment.
Using `GITHUB_PERSONAL_ACCESS_TOKEN` as `GH_TOKEN` allowed creation.

Issue URLs:

- #1 https://github.com/kako-jun/petit-collection/issues/1
- #2 https://github.com/kako-jun/petit-collection/issues/2
- #3 https://github.com/kako-jun/petit-collection/issues/3
- #4 https://github.com/kako-jun/petit-collection/issues/4
- #5 https://github.com/kako-jun/petit-collection/issues/5
- #6 https://github.com/kako-jun/petit-collection/issues/6
- #7 https://github.com/kako-jun/petit-collection/issues/7
- #8 https://github.com/kako-jun/petit-collection/issues/8
- #9 https://github.com/kako-jun/petit-collection/issues/9
- #10 https://github.com/kako-jun/petit-collection/issues/10
- #11 https://github.com/kako-jun/petit-collection/issues/11

## Priority bands

### Start now

These do not need another project to mature first:

1. #1 MVP umbrella: library + book split with HyperCard-like page interaction
2. #2 App shell and local-first persistence foundation
3. #3 Library asset model and browsing UI
4. #4 Book surface and page navigation
5. #5 Sticker page interactions: place, move, rotate, peel
6. #6 Ownership rules: one asset instance, one active placement
7. #7 PNG export for one book page

### Design now, implement later

These should be specified early but can wait on related projects:

8. #8 Sticker asset creation from imported images
9. #9 Stamp pipeline phase 1: import, cleanup, and reverse-from-rubber workflow
10. #10 Page theme system: sticker book, stamp book, scrapbook
11. #11 Exchange research: QR-based trust transfer without a central server

### Explicitly out of MVP

- custom scripting language
- cloud sync
- remote social platform features
- many page systems at once
- polished stamp extraction quality

## Blocker map

| Backlog item | Status | Depends on | Notes |
|---|---|---|---|
| #1 MVP umbrella | Ready | none | Product framing can start immediately |
| #2 App shell and persistence | Ready | none | Pure repo-local foundation |
| #3 Library asset model/UI | Ready | none | No external blocker |
| #4 Book surface and page navigation | Ready | none | HyperCard-like page model can start now |
| #5 Sticker page interactions | Ready | `mypace` (informing) | Can start now; polish may learn from `mypace` |
| #6 Ownership rules | Ready | none | Pure state-model work |
| #7 PNG export | Ready | none | Can start with current page contract |
| #8 Sticker asset creation | Partial | image-processing experiments | Basic version can start now; high-quality cutout is not locked |
| #9 Stamp pipeline phase 1 | Blocked-ish | not-yet-separated perspective-correction foundation | Perspective correction and cleanup likely need a dedicated base first |
| #10 Page theme system | Partial | none | Base abstraction can start now; richer themes can wait |
| #11 Exchange research | Partial | Nostr / exchange experiments | Metadata and trust model can start now; real protocol can wait |

## Issue drafts

## 1. MVP umbrella: library + book split with HyperCard-like page interaction (#1)

### Goal

Ship the first usable version of `petit-collection` as a local-first web app.

The MVP should prove the product split:

- `Library`: practical asset management
- `Book`: page-first arrangement experience

The HyperCard inspiration should apply to pages, not to the raw asset library.

### Status

Ready now.

### Depends on

- none

### MVP scope

- local asset storage
- image import
- simple sticker asset creation with white border
- one book with multiple pages
- sticker-book page interaction
- place / move / rotate / peel
- PNG export of one page

### Non-goals

- remote sync
- exchange/trading
- custom scripting language
- advanced stamp extraction
- multiple page systems at once

### Done when

A user can create a few sticker assets from local images, place them into a book,
rearrange them, peel them back into the library, and export a page as an image.

## 2. App shell and local-first persistence foundation (#2)

### Goal

Create the initial app shell and persistence layer for a local-first web app.

### Status

Ready now.

### Depends on

- none

### Scope

- choose and wire the frontend stack
- establish the app shell
- define local persistence entry points
- make stored data survive reloads

### Acceptance criteria

- app boots locally in dev mode
- a local persistence layer exists
- seed/test data can be stored and loaded after refresh
- the app structure can host both `Library` and `Book` surfaces

## 3. Library asset model and browsing UI (#3)

### Goal

Build the practical collection-management side of the product.

### Status

Ready now.

### Depends on

- none

### Scope

- define the `Asset` model for at least `sticker`, `stamp`, and `label`
- show assets in a browseable library surface
- support initial metadata display
- support search/filter/sort at least at a simple MVP level

### Acceptance criteria

- user can see all owned assets in one library view
- user can filter by kind
- user can sort by recent or title
- user can open an asset detail view or panel
- the library UI is clearly separate from the `Book` surface

## 4. Book surface and page navigation (#4)

### Goal

Create the `Book` surface where collected pieces are experienced as pages, not as a gallery.

### Status

Ready now.

### Depends on

- none

### Scope

- create one book model
- support multiple pages
- page navigation (flip or jump)
- auto-create new page when needed, or provide an explicit new-page path

### Acceptance criteria

- user can move from `Library` into `Book`
- user can browse multiple pages in one book
- page navigation feels like a book or album, not a file list
- the design leaves room for page-specific behavior later

## 5. Sticker page interactions: place, move, rotate, peel (#5)

### Goal

Make a sticker book page feel tactile and interactive.

### Status

Ready now, with later polish informed by `mypace`.

### Depends on

- no hard blocker
- `mypace` as a source of transform/rotation UX lessons

### Scope

- place an asset from the library onto a page
- drag to reposition
- rotate within a constrained range
- peel/remove from page back into library

### Acceptance criteria

- user can place a sticker onto a page
- user can move it after placement
- user can rotate it within the allowed range
- user can peel it off and return it to the library

## 6. Ownership rules: one asset instance, one active placement (#6)

### Goal

Preserve the make-believe real-world rule that one sticker instance cannot exist in two places at once.

### Status

Ready now.

### Depends on

- none

### Scope

- track ownership state for each asset
- prevent duplicate active placement of the same asset instance
- return the same instance to the library when peeled

### Acceptance criteria

- one asset cannot be placed on two pages at the same time
- after placement, the library reflects that the instance is already in use
- peeling the sticker returns that same instance to the library
- this rule is enforced in state, not just visually

## 7. PNG export for one book page (#7)

### Goal

Let the user export a composed page as a single image.

### Status

Ready now.

### Depends on

- none

### Scope

- render one page into a downloadable image
- preserve placement, rotation, and background theme
- produce an output usable for sharing or printing

### Acceptance criteria

- user can export the current page as PNG
- exported output matches the page composition closely enough for MVP
- the result is saved as a local file without any server dependency

## 8. Sticker asset creation from imported images (#8)

### Goal

Let the user import a local image and turn it into a sticker-like asset.

### Status

Partially blocked only for quality, not for a basic version.

### Depends on

- image-processing experiments elsewhere for higher-quality cutout rules

### Scope

- local image import
- basic sticker asset creation flow
- simple white-border treatment
- save the result into the library

### Acceptance criteria

- user can choose a local image file
- the app creates a stored sticker asset from it
- the created asset appears in the library immediately
- the result has at least a simple sticker-like white border presentation

## 9. Stamp pipeline phase 1: import, cleanup, and reverse-from-rubber workflow (#9)

### Goal

Add the first stamp-specific collection workflow after the sticker MVP is stable.

### Status

Design now, likely implement after a perspective-correction foundation is clarified or extracted.

### Depends on

- a not-yet-separated perspective-correction and cleanup foundation

### Scope

- import stamp photos
- basic background cleanup/transparent extraction
- support reverse-from-rubber capture flow
- optional simple recolor hook if cheap enough

### Current sample

- real photos currently exist at `input/stamp/`
- `IMG_20260503_204409.jpg` is confirmed as the front side
- `IMG_20260503_204338.jpg`, `204346.jpg`, and `204354.jpg` are reverse-side photos before inking
- they are mirrored relative to the stamped result

### Research split

Issue #9 should be treated as at least three internal tracks:

1. front-side photo extraction
2. reverse-side photo -> flip -> stamp-like image experiment
3. perspective correction / cleanup foundation for both paths

The second track is not just implementation work.
It is a proof-of-concept question:

Can we fake a usable stamp image from the reverse side without actually pressing ink?

One key rule for that experiment:

- the grooves in the rubber are expected to correspond to white paper in the final stamped image
- so the task is not just "invert tones" but "recover which regions are raised and which are recessed"

### First artifact

- experiment script: `scripts/reverse_stamp_poc.py`
- current output: `output/reverse-stamp-poc/`
- generated variants per image:
  - flipped
  - gray leveled
  - detail enhanced
  - binary mask
  - clean mask
  - pseudo blue ink
  - pseudo red ink
  - edge overlay

### Child issues

- #12 Front-side stamp extraction from photo sample
- #13 Reverse-side pre-ink stamp -> flipped pseudo-stamp proof of concept
- #14 Shared perspective correction and cleanup foundation for stamp photos

### Acceptance criteria

- a user can create a stamp asset from a photographed stamp source
- the app supports the reversed-rubber workflow in some form
- the resulting asset can be stored in the same library system
- the result can be placed onto book pages like other assets

## 10. Page theme system: sticker book, stamp book, scrapbook (#10)

### Goal

Define page types as behavior-rich surfaces rather than cosmetic backgrounds.

### Status

Base abstraction can start now; richer theme behavior can grow later.

### Depends on

- none for the abstraction
- future product learnings for final theme rules

### Scope

- create an abstraction for page-specific rules
- support at least these future themes:
  - sticker book page
  - stamp book page
  - scrapbook page
- keep room for different placement and layout constraints

### Acceptance criteria

- page behavior can vary by page type
- the architecture does not assume every page behaves like freeform sticker placement
- at least one future page type beyond the base sticker page can be added cleanly

## 11. Exchange research: QR-based trust transfer without a central server (#11)

### Goal

Research a believable first exchange flow that preserves the project's local-first philosophy.

### Status

Design now, implement protocol later.

### Depends on

- broader Nostr / exchange experiments if remote identity becomes relevant

### Scope

- explore QR-based transfer
- define what metadata moves with an asset
- model trust-based give-away interaction
- clarify what is social convention vs. technically enforced

### Acceptance criteria

- one candidate exchange flow is documented
- the model states what data is transferred
- the model states what cannot be cryptographically guaranteed in v1
- the flow fits the project's no-mandatory-server direction
