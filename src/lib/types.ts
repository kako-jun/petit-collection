// Domain types for petit-collection

export type AssetKind = 'sticker' | 'stamp' | 'label';

export type OwnershipState = 'library' | 'placed' | 'traded-away' | 'archived';

export interface Asset {
  id: string;
  kind: AssetKind;
  /** data URL or external URL */
  image: string;
  createdAt: string;
  sourceType: string;
  ownershipState: OwnershipState;
  // optional
  title?: string;
  tags?: string[];
  note?: string;
  captureDate?: string;
  originPlace?: string;
  givenBy?: string;
  visualStyle?: string;
}

export interface Placement {
  assetId: string;
  x: number;
  y: number;
  rotation: number;
  scale: number;
  zIndex: number;
}

export interface Page {
  id: string;
  pageType: 'sticker-book' | 'stamp-book' | 'scrapbook';
  background: string;
  placements: Placement[];
  decorations: unknown[];
}

export interface Book {
  id: string;
  title: string;
  theme: string;
  pages: Page[];
}
