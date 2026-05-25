# Overview

## Product

`petit-collection` is a digital sticker book and stamp book for children and collectors.
Instead of buying official goods, users can turn their own photos, drawings, and
stamp captures into collection pieces and arrange them into pages.

The emotional target is not "asset manager" but "a book I want to keep opening."

## Experience pillars

### 1. Make-believe collecting

Users create the feeling of owning rare or personal collection items from their own world:

- insects
- flowers
- ships
- original characters
- hand-drawn doodles
- travel stamps

### 2. Local-first ownership

The collection belongs to the user device.
There is no mandatory account, server storage, or subscription.

### 3. Book-first presentation

The app should feel like:

- a sticker album
- a stamp notebook
- a scrapbook
- a moodboard binder

not like a spreadsheet or media gallery.

## Information architecture

The product should be split into two major surfaces.

### Library

Purpose:
- import assets
- inspect assets
- search/filter/sort
- see metadata and history
- choose what to place

Mental model:
- collection shelf
- drawer
- stock box

### Book

Purpose:
- place assets on pages
- browse pages
- rearrange composition
- feel the collection as a crafted object

Mental model:
- album
- notebook
- card book

## HyperCard-like interpretation

The HyperCard inspiration should be applied to the `Book` layer, not the entire app.

Why:

- asset management needs density and practicality
- the emotional value comes from page interaction
- page themes naturally map to different behaviors

This gives us a useful rule:

> Assets are data-rich. Pages are behavior-rich.

### Pages as "small worlds"

A page may define:

- placement rules
- background theme
- available decorations
- snapping/fixed slots/freeform behavior
- export framing

Examples:

- `StickerBookPage`: free placement, light rotation, playful overlap
- `StampBookPage`: grid or slot-oriented, lower rotation freedom
- `ScrapbookPage`: supports text labels and collage composition

## Why this matters

Without this split, the app risks becoming either:

- just another board/canvas app
- just another image catalog

With this split, `petit-collection` can compete on both:

- utility for managing collected pieces
- delight when presenting and arranging them
