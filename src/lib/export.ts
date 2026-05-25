import html2canvas from 'html2canvas';

/**
 * Export the book-surface element as a PNG download.
 * Returns true if export succeeded, false otherwise.
 *
 * Note on useCORS: currently all images are IndexedDB data URLs (no CORS needed).
 * If external URLs are added in the future, the image element must also set
 * crossorigin="anonymous" and the server must allow CORS.
 */
export async function exportPageAsPng(
  surface: HTMLElement,
  filename = 'petit-collection-page.png',
): Promise<boolean> {
  try {
    const canvas = await html2canvas(surface, {
      useCORS: true,
      backgroundColor: null,
      scale: 2, // 2× for sharper (Retina-friendly) output
      ignoreElements: (el) =>
        el.classList.contains('book-surface-label') ||
        el.classList.contains('peel-btn'),
    });

    const url = canvas.toDataURL('image/png');
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    // Append to DOM for Firefox compatibility
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    return true;
  } catch (e) {
    console.error('PNG export failed', e);
    return false;
  }
}

/** Sanitize a string for use as a filename component. */
export function safeFilename(s: string): string {
  return s
    .replace(/[^\w\u3040-\u9FFF-]/g, '_')
    .replace(/_+/g, '_')
    .slice(0, 60);
}
