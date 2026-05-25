# Spec

## Scope

This document defines the initial product model for `petit-collection`.

## Domain model

### Asset

A collectible piece owned by the user.

Kinds:

- `sticker`
- `stamp`
- `label`

Required fields:

- `id`
- `kind`
- `image`
- `createdAt`
- `sourceType`
- `ownershipState`

Optional fields:

- `title`
- `tags`
- `note`
- `captureDate`
- `originPlace`
- `givenBy`
- `visualStyle`

### OwnershipState

- `library`
- `placed`
- `traded-away`
- `archived`

## Book model

### Book

A collection of pages with a theme.

Fields:

- `id`
- `title`
- `theme`
- `pages[]`

### Page

A themed surface where assets are placed.

Fields:

- `id`
- `pageType`
- `background`
- `placements[]`
- `decorations[]`

### Placement

Placement of one asset on a page.

Fields:

- `assetId`
- `x`
- `y`
- `rotation`
- `scale`
- `zIndex`

## Interaction rules

### Asset lifecycle

1. User imports or creates an asset
2. Asset enters the library
3. User places the asset onto a page
4. Asset becomes unavailable for duplicate placement while placed
5. User may peel it off and return it to the library

### Real-world flavored constraints

- One asset instance cannot be placed twice at the same time
- To own two similar stickers, the user must create/import two assets
- Scaling should be limited to preserve sticker-like believability
- Peeling returns the same asset instance, not a copy

## Product surfaces

### Library requirements

- grid/list browsing
- filter by kind
- sort by recent/oldest/title
- search by title/tag/note
- asset detail view
- "place into book" action

### Book requirements

- page flip or page jump navigation
- place asset from library
- drag to reposition
- rotate within constrained range
- peel/remove back to library
- auto-create new page when needed

## Page types

### Sticker book page

- free placement
- mild rotation freedom
- playful composition

### Stamp book page

- slot/grid-friendly
- less rotation
- more orderly feel

### Scrapbook page

- free placement
- labels and notes
- denser collage potential

## MVP

The MVP should include:

- local asset storage
- image import
- sticker asset creation with simple white border
- one book with multiple pages
- sticker book page interaction
- place / move / rotate / peel
- PNG export of one page

The MVP should not include yet:

- network sync
- remote trading
- custom scripting language
- many page types at once
- advanced stamp extraction pipeline

## Non-goals for v1 planning

- HyperCard-compatible scripting
- user-authored page logic language
- marketplace/social feed
- cloud-only storage
