# Research Notes

## Positioning

`petit-collection` is not just a canvas app and not just a gallery.
Its value comes from combining:

- collectible asset management
- page-based arrangement
- playful ownership rules

## HyperCard direction

The most useful interpretation is:

- do not turn every asset into a mini app
- do turn the `Book` surface into a behavior-rich page system

That keeps the collection practical while preserving the album feeling.

## Nearby products and ideas

### HyperCard descendants

- `Stacksmith` and `ViperCard` matter as inspiration for page-centric interaction
- `Decker` matters as a reminder that expressive page systems drift toward zine / story tooling

For `petit-collection`, this means:

- page-centric interaction is valuable
- a custom scripting language is not an MVP requirement

### Card-based collection or task metaphors

There are many products where a card is a unit of work or a unit of content.
That does not automatically solve the "book I want to reopen" problem.

The differentiator here is the combination of:

- asset scarcity rules
- tactile placement
- themed pages
- local-first ownership

## Dependency observations

### Perspective-correction foundation (not yet separated)

Likely informs:

- stamp capture perspective correction
- cleanup path for angled photos

Meaning:

- the first sticker MVP should not wait for that foundation
- stamp-specific import quality probably should

### Current real sample set

As of 2026-05-25, there is a real stamp-photo sample set stored outside this repo at:

- [freeza/input/stamp](/home/d131/repos/private/freeza/input/stamp:1)

Observed files:

- `IMG_20260503_204338.jpg`
- `IMG_20260503_204346.jpg`
- `IMG_20260503_204354.jpg`
- `IMG_20260503_204409.jpg`

Known notes:

- `IMG_20260503_204409.jpg` is the front side (`表側`)
- the other three images are reverse-side views taken before inking
- they are mirrored relative to the stamped result

This means issue #9 should not stay purely abstract anymore.
The first stamp-pipeline design can and should refer to this concrete sample set.

### New experiment implied by the sample set

There is now a concrete research question:

Can a reverse-side, pre-ink stamp photo be converted into a believable stamp image
without physically pressing it onto paper?

That breaks the stamp path into at least two subproblems:

- reverse-side extraction and horizontal flip
- "inked stamp" appearance synthesis from an uninked rubber surface photo

One crucial semantic rule must be preserved:

- grooves in the rubber surface should become white paper in the stamped result
- the inked parts come from the raised surface, not from the grooves themselves

The first one is structural.
The second one is a real experiment and may fail, but it is valuable enough to deserve
its own explicit task framing.

### First POC run

There is now a reproducible experiment script:

- `scripts/reverse_stamp_poc.py`

It currently generates these stages for each reverse-side sample:

- `01_flipped`
- `02_gray_levels`
- `03_detail`
- `04_binary_mask`
- `05_clean_mask`
- `06_pseudo_blue`
- `07_pseudo_red`
- `08_edge_overlay`

The output directory is:

- `output/reverse-stamp-poc/`

This is not the final extraction pipeline.
It is the first proof-of-concept pass for issue #13.

### `mypace`

Likely informs:

- rotation UX
- transform feel for placed items

Meaning:

- page placement can start before `mypace`
- final interaction polish should absorb lessons from it

### `Nostr` or exchange-related work

Likely informs:

- remote or semi-remote exchange
- identity / provenance experiments

Meaning:

- exchange should not block the core collection MVP
- ownership metadata should still be modeled early

## Main conclusion

The repository should distinguish three kinds of work:

1. work that can start immediately inside `petit-collection`
2. work that should be designed now but implemented after another project matures
3. work that must stay explicitly out of MVP

That distinction is captured in `docs/issue-backlog.md`.
