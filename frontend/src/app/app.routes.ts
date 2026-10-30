import type { Routes, UrlMatchResult, UrlSegment } from '@angular/router';
import { ShellComponent } from './layout/shell.component';

/**
 * The routes. Each page sits in `ShellComponent` and loads lazily. `data.fill` makes a page
 * fill the free height of the viewport.
 */
export const routes: Routes = [
  {
    path: '',
    component: ShellComponent,
    children: [
      {
        path: '',
        pathMatch: 'full',
        redirectTo: () => LEGACY_HASHES[window.location.hash] ?? '/live',
      },
      {
        path: 'live',
        title: 'Live · Gangway',
        data: { fill: true },
        loadComponent: () => import('./pages/live/live.page').then((m) => m.LivePage),
      },
      {
        path: 'animation',
        title: 'Animation · Gangway',
        loadComponent: () =>
          import('./pages/animation/animation.page').then((m) => m.AnimationPage),
      },
      {
        matcher: presetsMatcher,
        title: 'Presets · Gangway',
        data: { fill: true },
        loadComponent: () => import('./pages/presets/presets.page').then((m) => m.PresetsPage),
      },
      { path: '**', redirectTo: 'live' },
    ],
  },
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
