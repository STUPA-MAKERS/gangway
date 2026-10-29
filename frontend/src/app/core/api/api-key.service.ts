import { DOCUMENT } from '@angular/common';
import { Injectable, inject, signal } from '@angular/core';

const STORAGE_KEY = 'apiKey';

/**
 * The API key of the browser.
 *
 * The app sends requests with no key first. Through the SSO tunnel nginx adds the key, so
 * the browser never needs one there. On the LAN the backend refuses a request with no key.
 * The app then asks the user for the key and keeps it in `localStorage`.
 *
 * A link can give the key in the query parameter `apiKey`. The service keeps it and
 * removes it from the address bar, so the key does not stay in the history.
 */
@Injectable({ providedIn: 'root' })
export class ApiKeyService {
  private readonly document = inject(DOCUMENT);
  private readonly _key = signal<string | null>(this.read());

  /** The stored key, or null. */
  readonly key = this._key.asReadonly();

  /** True after the backend refused a request. The shell then asks for a key. */
  readonly refused = signal(false);

  constructor() {
    this.takeFromUrl();
  }

  set(key: string): void {
    const value = key.trim();
    this._key.set(value || null);
    this.write(value || null);
  }

  clear(): void {
    this._key.set(null);
    this.write(null);
  }

  private takeFromUrl(): void {
    const location = this.document.defaultView?.location;
    if (!location) return;
    const url = new URL(location.href);
    const key = url.searchParams.get('apiKey');
    if (!key) return;
    this.set(key);
    url.searchParams.delete('apiKey');
    this.document.defaultView?.history.replaceState(
      {},
      this.document.title,
      `${url.pathname}${url.search}${url.hash}`,
    );
  }

  private read(): string | null {
    try {
      return localStorage.getItem(STORAGE_KEY);
    } catch {
      return null;
    }
  }

  private write(key: string | null): void {
    try {
      if (key) localStorage.setItem(STORAGE_KEY, key);
      else localStorage.removeItem(STORAGE_KEY);
    } catch {
      /* A private window can refuse the storage. The key then lasts for this page only. */
    }
  }
}
