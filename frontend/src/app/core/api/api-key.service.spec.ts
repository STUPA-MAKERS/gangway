import { TestBed } from '@angular/core/testing';
import { ApiKeyService } from './api-key.service';

describe('ApiKeyService', () => {
  beforeEach(() => {
    localStorage.clear();
    window.history.replaceState({}, '', '/');
  });

  // §F/web-ui/access/000090
  it('stores the key of the link and removes it from the address', () => {
    window.history.replaceState({}, '', '/presets?apiKey=secret&x=1#top');

    const keys = TestBed.inject(ApiKeyService);

    expect(keys.key()).toBe('secret');
    expect(localStorage.getItem('apiKey')).toBe('secret');
    expect(window.location.pathname).toBe('/presets');
    expect(window.location.search).toBe('?x=1');
    expect(window.location.hash).toBe('#top');
  });

  // §F/web-ui/access/000090
  it('keeps the address of a link without a key', () => {
    window.history.replaceState({}, '', '/live?x=1');

    const keys = TestBed.inject(ApiKeyService);

    expect(keys.key()).toBeNull();
    expect(window.location.search).toBe('?x=1');
  });
});
