import { TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { LEGACY_HASHES, routes } from './app.routes';

describe('routes', () => {
  // §F/web-ui/navigation/000091
  it('maps the hash links of the old app to the new routes', () => {
    expect(LEGACY_HASHES).toEqual({
      '#viz': '/live',
      '#animations': '/animation',
      '#presets': '/presets',
    });
  });

  // §F/web-ui/navigation/000091
  it('redirects the root with an old hash to its new route', async () => {
    window.history.replaceState({}, '', '/#presets');
    TestBed.configureTestingModule({ providers: [provideRouter(routes)] });
    const router = TestBed.inject(Router);

    await router.navigateByUrl('/');

    expect(router.url).toBe('/presets');
  });

  // §F/web-ui/navigation/000091
  it('sends an unknown path to the live view', async () => {
    window.history.replaceState({}, '', '/');
    TestBed.configureTestingModule({ providers: [provideRouter(routes)] });
    const router = TestBed.inject(Router);

    await router.navigateByUrl('/nothing/here');

    expect(router.url).toBe('/live');
  });
});
