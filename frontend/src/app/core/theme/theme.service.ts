import { DOCUMENT } from '@angular/common';
import { Injectable, computed, inject, signal } from '@angular/core';

export type ThemePreference = 'light' | 'dark' | 'system';
export type ResolvedTheme = 'light' | 'dark';

const STORAGE_KEY = 'gangway.theme';

/** The page background of each theme (`--color-bg` of the kit), for the `theme-color` tag. */
export const THEME_COLOR: Record<ResolvedTheme, string> = {
  light: '#f6f7f5',
  dark: '#101211',
};

/**
 * The theme: `system` follows the operating system, `light` and `dark` are fixed. The
 * service keeps the preference in `localStorage` and writes the theme to `data-theme` on
 * `<html>`, which the tokens of the kit read.
 */
@Injectable({ providedIn: 'root' })
export class ThemeService {
  private readonly document = inject(DOCUMENT);
  private readonly media = window.matchMedia('(prefers-color-scheme: dark)');
  private readonly _preference = signal<ThemePreference>(this.readStored());
  private readonly systemDark = signal(this.media.matches);

  readonly preference = this._preference.asReadonly();

  readonly resolved = computed<ResolvedTheme>(() => {
    const pref = this._preference();
    if (pref === 'system') return this.systemDark() ? 'dark' : 'light';
    return pref;
  });

  /** Call this once at the app start. */
  init(): void {
    this.media.addEventListener('change', (e) => {
      this.systemDark.set(e.matches);
      this.apply();
    });
    this.apply();
  }

  /** Switches between light and dark, from the theme that is visible now. */
  toggle(): void {
    const next: ThemePreference = this.resolved() === 'dark' ? 'light' : 'dark';
    this._preference.set(next);
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      /* The theme then lasts for this page only. */
    }
    this.apply();
  }

  private apply(): void {
    const theme = this.resolved();
    this.document.documentElement.setAttribute('data-theme', theme);
    this.document
      .querySelectorAll<HTMLMetaElement>('meta[name="theme-color"]')
      .forEach((meta) => meta.setAttribute('content', THEME_COLOR[theme]));
  }

  private readStored(): ThemePreference {
    try {
      const v = localStorage.getItem(STORAGE_KEY);
      if (v === 'light' || v === 'dark' || v === 'system') return v;
    } catch {
      /* No storage: use the system theme. */
    }
    return 'system';
  }
}
