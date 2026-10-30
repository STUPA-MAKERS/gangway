import type { Routes, UrlMatchResult, UrlSegment } from '@angular/router';

/**
 * The routes. Each page loads lazily into the outlet of the kit shell (`App`). The route
 * data `wide` lifts the width cap of the shell, because each page sets its own width.
 * `fill` makes a page fill the free height of the viewport.
 */
export const routes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    redirectTo: () => LEGACY_HASHES[window.location.hash] ?? '/live',
  },
  {
    path: 'live',
    title: 'Live · Gangway',
    data: { wide: true, fill: true },
    loadComponent: () => import('./pages/live/live.page').then((m) => m.LivePage),
  },
  {
    path: 'animation',
    title: 'Animation · Gangway',
    data: { wide: true },
    loadComponent: () => import('./pages/animation/animation.page').then((m) => m.AnimationPage),
  },
  {
    matcher: presetsMatcher,
    title: 'Presets · Gangway',
    data: { wide: true, fill: true },
    loadComponent: () => import('./pages/presets/presets.page').then((m) => m.PresetsPage),
  },
  {
    path: 'stats',
    title: 'Statistics · Gangway',
    data: { wide: true },
    loadComponent: () => import('./pages/stats/stats.page').then((m) => m.StatsPage),
  },
  { path: '**', redirectTo: 'live' },
];

/** The hash links of the old Next.js app (`/#viz`), with their new route. */
export const LEGACY_HASHES: Record<string, string> = {
  '#viz': '/live',
  '#animations': '/animation',
  '#presets': '/presets',
};

/**
 * Matches `/presets` and `/presets/:name` with one route. The page stays when a preset
 * opens or closes, so the list keeps its scroll position. The name goes to the `name`
 * input of the page.
 */
export function presetsMatcher(segments: UrlSegment[]): UrlMatchResult | null {
  if (segments[0]?.path !== 'presets' || segments.length > 2) return null;
  const name = segments[1];
  return { consumed: segments, posParams: name ? { name } : {} };
}
