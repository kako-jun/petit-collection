import type { Asset, AssetKind } from './types';

/** Escape user-controlled strings before inserting into innerHTML. */
function esc(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

const KIND_LABEL: Record<string, string> = {
  sticker: '🧩 sticker',
  stamp: '🔖 stamp',
  label: '🏷 label',
};

export function renderAssetGrid(container: HTMLElement, assets: Asset[]): void {
  if (assets.length === 0) {
    container.innerHTML =
      '<p class="empty">No assets yet. Press "Add seed data" to get started.</p>';
    return;
  }

  container.innerHTML = assets
    .map((a) => {
      const label = esc(a.title ?? a.id);
      const thumb = a.image
        ? `<img src="${esc(a.image)}" alt="${esc(a.title ?? '')}">`
        : '?';
      return `
        <div class="asset-card" data-id="${esc(a.id)}" tabindex="0" role="button" aria-label="${label}">
          <div class="asset-thumb ${esc(a.kind)}">${thumb}</div>
          <div class="asset-meta">
            <span class="asset-title">${label}</span>
            <span class="asset-kind">${esc(KIND_LABEL[a.kind] ?? a.kind)}</span>
            <span class="asset-state ${esc(a.ownershipState)}">${esc(a.ownershipState)}</span>
          </div>
        </div>
      `;
    })
    .join('');
}

export type SortKey = 'recent' | 'oldest' | 'title';

export function filterAndSort(
  assets: Asset[],
  kind: AssetKind | 'all',
  sort: SortKey,
  query: string,
): Asset[] {
  let result = assets.slice();

  // filter by kind
  if (kind !== 'all') {
    result = result.filter((a) => a.kind === kind);
  }

  // filter by search query (title / tags / note)
  if (query.trim()) {
    const q = query.trim().toLowerCase();
    result = result.filter(
      (a) =>
        (a.title ?? '').toLowerCase().includes(q) ||
        (a.tags ?? []).some((t) => t.toLowerCase().includes(q)) ||
        (a.note ?? '').toLowerCase().includes(q),
    );
  }

  // sort
  switch (sort) {
    case 'recent':
      result.sort((a, b) => b.createdAt.localeCompare(a.createdAt));
      break;
    case 'oldest':
      result.sort((a, b) => a.createdAt.localeCompare(b.createdAt));
      break;
    case 'title':
      result.sort((a, b) => (a.title ?? a.id).localeCompare(b.title ?? b.id));
      break;
  }

  return result;
}

export function renderDetailPanel(panel: HTMLElement, asset: Asset | null): void {
  if (!asset) {
    panel.hidden = true;
    return;
  }
  panel.hidden = false;

  const thumb = asset.image
    ? `<img src="${esc(asset.image)}" alt="${esc(asset.title ?? '')}">`
    : '?';

  const optionalRows = [
    asset.title ? `<dt>Title</dt><dd>${esc(asset.title)}</dd>` : '',
    asset.tags?.length ? `<dt>Tags</dt><dd>${esc(asset.tags.join(', '))}</dd>` : '',
    asset.note ? `<dt>Note</dt><dd>${esc(asset.note)}</dd>` : '',
    asset.originPlace ? `<dt>Origin</dt><dd>${esc(asset.originPlace)}</dd>` : '',
    asset.captureDate ? `<dt>Captured</dt><dd>${esc(asset.captureDate)}</dd>` : '',
    asset.givenBy ? `<dt>Given by</dt><dd>${esc(asset.givenBy)}</dd>` : '',
  ]
    .filter(Boolean)
    .join('');

  panel.innerHTML = `
    <button class="detail-close" aria-label="Close" id="detail-close">✕</button>
    <div class="detail-thumb ${esc(asset.kind)}">${thumb}</div>
    <dl class="detail-fields">
      <dt>ID</dt><dd>${esc(asset.id)}</dd>
      <dt>Kind</dt><dd>${esc(KIND_LABEL[asset.kind] ?? asset.kind)}</dd>
      <dt>Status</dt><dd class="asset-state ${esc(asset.ownershipState)}">${esc(asset.ownershipState)}</dd>
      ${optionalRows}
      <dt>Created</dt><dd>${esc(new Date(asset.createdAt).toLocaleDateString())}</dd>
    </dl>
  `;
}
