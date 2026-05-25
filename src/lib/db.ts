import localforage from 'localforage';
import type { Asset, Book, Page } from './types';

const store = localforage.createInstance({
  name: 'petit-collection',
  storeName: 'data',
});

const ASSETS_KEY = 'assets';
const BOOK_KEY = 'book';

// --- Assets ---

export async function loadAssets(): Promise<Asset[]> {
  return (await store.getItem<Asset[]>(ASSETS_KEY)) ?? [];
}

export async function saveAssets(assets: Asset[]): Promise<void> {
  await store.setItem(ASSETS_KEY, assets);
}

export async function clearAssets(): Promise<void> {
  await store.removeItem(ASSETS_KEY);
}

// --- Book ---

export async function loadBook(): Promise<Book | null> {
  return store.getItem<Book>(BOOK_KEY);
}

export async function saveBook(book: Book): Promise<void> {
  await store.setItem(BOOK_KEY, book);
}

/** Add a blank page to the book and persist. */
export async function addPage(book: Book): Promise<Book> {
  const newPage: Page = {
    id: `page-${Date.now()}`,
    pageType: 'sticker-book',
    background: '#fffdf6',
    placements: [],
    decorations: [],
  };
  const updated: Book = { ...book, pages: [...book.pages, newPage] };
  await saveBook(updated);
  return updated;
}

// --- Seed ---

export async function seedLibrary(): Promise<void> {
  const existing = await loadAssets();
  if (existing.length > 0) return;

  const assets: Asset[] = [
    {
      id: 'seed-001',
      kind: 'sticker',
      image: '',
      createdAt: new Date().toISOString(),
      sourceType: 'manual',
      ownershipState: 'library',
      title: 'Sample sticker A',
      tags: ['sample', 'sticker'],
    },
    {
      id: 'seed-002',
      kind: 'stamp',
      image: '',
      createdAt: new Date().toISOString(),
      sourceType: 'photo',
      ownershipState: 'library',
      title: 'Travel stamp — Kyoto',
      tags: ['travel', 'stamp', 'kyoto'],
      originPlace: 'Kyoto',
    },
    {
      id: 'seed-003',
      kind: 'label',
      image: '',
      createdAt: new Date().toISOString(),
      sourceType: 'manual',
      ownershipState: 'library',
      title: 'Handwritten label',
      tags: ['label'],
    },
  ];
  await saveAssets(assets);

  const book: Book = {
    id: 'book-001',
    title: 'My first book',
    theme: 'default',
    pages: [
      {
        id: 'page-001',
        pageType: 'sticker-book',
        background: '#fffdf6',
        placements: [],
        decorations: [],
      },
      {
        id: 'page-002',
        pageType: 'stamp-book',
        background: '#f0f4f8',
        placements: [],
        decorations: [],
      },
    ],
  };
  await saveBook(book);
}
