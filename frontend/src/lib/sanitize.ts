import DOMPurify from "dompurify";

/**
 * Sanitize HTML string to prevent XSS attacks.
 * Use when rendering user-generated content.
 */
export function sanitizeHtml(dirty: string): string {
  if (typeof window === "undefined") return dirty;
  return DOMPurify.sanitize(dirty, {
    ALLOWED_TAGS: ["b", "i", "em", "strong", "a", "p", "br", "ul", "ol", "li"],
    ALLOWED_ATTR: ["href", "target", "rel"],
  });
}

/**
 * Sanitize plain text — strip all HTML tags.
 */
export function sanitizeText(dirty: string): string {
  if (typeof window === "undefined") return dirty;
  return DOMPurify.sanitize(dirty, { ALLOWED_TAGS: [] });
}
