import type { Asset, Book, Page, Placement } from './types';
import { saveBook, saveAssets } from './db';

/** Rotation constraint for sticker-book pages (degrees). */
const MAX_ROTATION_DEG = 30;

/** Clamp rotation to the allowed range. */
function clampRotation(deg: number): number {
  return Math.max(-MAX_ROTATION_DEG, Math.min(MAX_ROTATION_DEG, deg));
}

/**
 * Activate sticker-book interactions on the placement-layer of a page.
 * Returns a cleanup function to remove all listeners.
 */
export function activateStickerPage(
  layer: HTMLElement,
  page: Page,
  book: Book,
  assets: Asset[],
  onUpdate: (updatedBook: Book) => void,
): () => void {
  const cleanups: (() => void)[] = [];

  // Render existing placements
  renderPlacements(layer, page, assets, book, onUpdate, cleanups);

  return () => cleanups.forEach((fn) => fn());
}

function renderPlacements(
  layer: HTMLElement,
  page: Page,
  assets: Asset[],
  book: Book,
  onUpdate: (updatedBook: Book) => void,
  cleanups: (() => void)[],
) {
  layer.innerHTML = '';

  for (const pl of page.placements) {
    const asset = assets.find((a) => a.id === pl.assetId);
    if (!asset) continue;
    const el = createPlacedElement(asset, pl);
    layer.appendChild(el);
    const unsub = attachDragRotate(el, pl, page, book, assets, onUpdate);
    cleanups.push(unsub);
  }
}

function createPlacedElement(asset: Asset, pl: Placement): HTMLElement {
  const el = document.createElement('div');
  el.className = 'placed-asset';
  el.dataset.assetId = asset.id;
  el.style.cssText = placementToCSS(pl);
  el.setAttribute('role', 'button');
  el.setAttribute('tabindex', '0');
  el.setAttribute('aria-label', asset.title ?? asset.id);

  const inner = document.createElement('div');
  inner.className = `asset-thumb ${asset.kind}`;
  inner.textContent = asset.image ? '' : '?';
  if (asset.image) {
    const img = document.createElement('img');
    img.src = asset.image;
    img.alt = asset.title ?? '';
    inner.appendChild(img);
  }
  el.appendChild(inner);

  const peel = document.createElement('button');
  peel.className = 'peel-btn';
  peel.setAttribute('aria-label', 'Peel off');
  peel.textContent = '✕';
  el.appendChild(peel);

  return el;
}

function placementToCSS(pl: Placement): string {
  return [
    `position:absolute`,
    `left:${pl.x}px`,
    `top:${pl.y}px`,
    `transform:rotate(${pl.rotation}deg) scale(${pl.scale})`,
    `z-index:${pl.zIndex}`,
    `width:100px`,
    `height:100px`,
    `cursor:grab`,
    `user-select:none`,
    `touch-action:none`,
  ].join(';');
}

function attachDragRotate(
  el: HTMLElement,
  pl: Placement,
  page: Page,
  book: Book,
  assets: Asset[],
  onUpdate: (updatedBook: Book) => void,
): () => void {
  const peel = el.querySelector('.peel-btn')!;

  // --- Peel ---
  const onPeel = (e: Event) => {
    e.stopPropagation();
    peelAsset(pl.assetId, page, book, assets, onUpdate);
  };
  peel.addEventListener('click', onPeel);

  // --- Drag (pointer events) ---
  let dragging = false;
  let startX = 0;
  let startY = 0;
  let originX = pl.x;
  let originY = pl.y;

  const onPointerDown = (e: PointerEvent) => {
    if ((e.target as HTMLElement).closest('.peel-btn')) return;
    dragging = true;
    startX = e.clientX;
    startY = e.clientY;
    originX = pl.x;
    originY = pl.y;
    el.setPointerCapture(e.pointerId);
    el.style.cursor = 'grabbing';
    e.preventDefault();
  };

  const onPointerMove = (e: PointerEvent) => {
    if (!dragging) return;
    const dx = e.clientX - startX;
    const dy = e.clientY - startY;
    pl.x = originX + dx;
    pl.y = originY + dy;
    el.style.left = `${pl.x}px`;
    el.style.top = `${pl.y}px`;
  };

  const onPointerUp = async () => {
    if (!dragging) return;
    dragging = false;
    el.style.cursor = 'grab';
    await persistBook(book, onUpdate);
  };

  // --- Rotate (wheel) ---
  const onWheel = async (e: WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 5 : -5;
    pl.rotation = clampRotation(pl.rotation + delta);
    el.style.transform = `rotate(${pl.rotation}deg) scale(${pl.scale})`;
    await persistBook(book, onUpdate);
  };

  el.addEventListener('pointerdown', onPointerDown);
  el.addEventListener('pointermove', onPointerMove);
  el.addEventListener('pointerup', onPointerUp);
  el.addEventListener('pointercancel', onPointerUp); // release drag on cancel
  el.addEventListener('wheel', onWheel, { passive: false });

  return () => {
    peel.removeEventListener('click', onPeel);
    el.removeEventListener('pointerdown', onPointerDown);
    el.removeEventListener('pointermove', onPointerMove);
    el.removeEventListener('pointerup', onPointerUp);
    el.removeEventListener('pointercancel', onPointerUp);
    el.removeEventListener('wheel', onWheel);
  };
}

async function persistBook(
  book: Book,
  onUpdate: (updatedBook: Book) => void,
): Promise<void> {
  try {
    await saveBook(book);
    onUpdate(book);
  } catch (e) {
    console.error('Failed to save book', e);
  }
}

function peelAsset(
  assetId: string,
  page: Page,
  book: Book,
  assets: Asset[],
  onUpdate: (updatedBook: Book) => void,
) {
  // Remove placement from page
  page.placements = page.placements.filter((p) => p.assetId !== assetId);
  // Return asset to library state
  const asset = assets.find((a) => a.id === assetId);
  if (asset) asset.ownershipState = 'library';
  // Persist both book (placement removed) and assets (ownershipState changed)
  void Promise.all([saveBook(book), saveAssets(assets)])
    .then(() => onUpdate(book))
    .catch((e) => console.error('Failed to save after peel', e));
}

/**
 * Place an asset onto a page at the given position.
 * Enforces the one-instance rule via both ownershipState and placement scan.
 * Returns false if the asset is already placed anywhere.
 */
export function placeAsset(
  asset: Asset,
  page: Page,
  book: Book,
  x: number,
  y: number,
): boolean {
  // Primary guard: ownershipState (fast path)
  if (asset.ownershipState !== 'library') return false;

  // Secondary guard: scan all pages for an existing placement (defensive)
  const alreadyPlaced = book.pages.some((pg) =>
    pg.placements.some((pl) => pl.assetId === asset.id),
  );
  if (alreadyPlaced) return false;

  const placement: Placement = {
    assetId: asset.id,
    x,
    y,
    rotation: 0,
    scale: 1,
    zIndex: page.placements.length + 1,
  };
  page.placements.push(placement);
  asset.ownershipState = 'placed';
  return true;
}
