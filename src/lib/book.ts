import type { Book, Page } from './types';

/** Render the book navigator: page tabs + current page surface. */
export function renderBook(
  container: HTMLElement,
  book: Book,
  currentIndex: number,
  onNavigate: (index: number) => void,
  onAddPage: () => void,
): void {
  const page = book.pages[currentIndex];
  if (!page) return;

  container.innerHTML = `
    <div class="book-nav" role="tablist" aria-label="Pages">
      ${book.pages
        .map(
          (_p, i) => `
        <button class="page-tab ${i === currentIndex ? 'active' : ''}"
                role="tab"
                aria-selected="${i === currentIndex}"
                data-index="${i}"
                aria-label="Page ${i + 1}">
          ${i + 1}
        </button>
      `,
        )
        .join('')}
      <button class="page-tab page-add" id="btn-add-page" aria-label="Add page">+</button>
    </div>
    <div class="book-surface" style="background:${page.background}" data-page-id="${page.id}" data-page-type="${page.pageType}">
      <div class="book-surface-label">${pageTypeLabel(page)} · page ${currentIndex + 1} of ${book.pages.length}</div>
      <div id="placement-layer" class="placement-layer"></div>
    </div>
    <div class="book-page-actions">
      <button id="btn-prev" ${currentIndex === 0 ? 'disabled' : ''}>← Prev</button>
      <span class="book-page-counter">${currentIndex + 1} / ${book.pages.length}</span>
      <button id="btn-next" ${currentIndex === book.pages.length - 1 ? 'disabled' : ''}>Next →</button>
    </div>
  `;

  // wire tab clicks (guard index range in callback)
  container.querySelectorAll<HTMLButtonElement>('.page-tab[data-index]').forEach((btn) => {
    btn.addEventListener('click', () => onNavigate(Number(btn.dataset.index)));
  });

  // wire add-page button
  container.querySelector('#btn-add-page')?.addEventListener('click', onAddPage);

  container.querySelector('#btn-prev')?.addEventListener('click', () =>
    onNavigate(currentIndex - 1),
  );
  container.querySelector('#btn-next')?.addEventListener('click', () =>
    onNavigate(currentIndex + 1),
  );
}

function pageTypeLabel(page: Page): string {
  // Use Page['pageType'] to ensure map stays in sync with the union type.
  const map: Record<Page['pageType'], string> = {
    'sticker-book': 'Sticker book',
    'stamp-book': 'Stamp book',
    scrapbook: 'Scrapbook',
  };
  return map[page.pageType];
}
