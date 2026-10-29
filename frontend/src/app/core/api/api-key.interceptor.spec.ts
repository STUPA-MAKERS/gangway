import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { apiKeyInterceptor } from './api-key.interceptor';
import { ApiKeyService } from './api-key.service';

describe('apiKeyInterceptor', () => {
  let http: HttpClient;
  let backend: HttpTestingController;
  let keys: ApiKeyService;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([apiKeyInterceptor])),
        provideHttpClientTesting(),
      ],
    });
    http = TestBed.inject(HttpClient);
    backend = TestBed.inject(HttpTestingController);
    keys = TestBed.inject(ApiKeyService);
  });

  afterEach(() => backend.verify());

  it('sends no key while none is stored, so nginx can add it', () => {
    http.get('/api/config/').subscribe();
    const req = backend.expectOne('/api/config/');
    expect(req.request.headers.has('X-API-Key')).toBe(false);
    req.flush({});
  });

  it('sends the stored key', () => {
    keys.set('secret');
    http.get('/api/config/').subscribe();
    const req = backend.expectOne('/api/config/');
    expect(req.request.headers.get('X-API-Key')).toBe('secret');
    expect(localStorage.getItem('apiKey')).toBe('secret');
    req.flush({});
  });

  it('marks the key as refused on 403', () => {
    http.get('/api/config/').subscribe({ error: () => undefined });
    backend.expectOne('/api/config/').flush({ detail: 'Invalid API Key' }, { status: 403, statusText: 'Forbidden' });
    expect(keys.refused()).toBe(true);
  });

  it('leaves other URLs alone', () => {
    keys.set('secret');
    http.get('/manifest.webmanifest').subscribe();
    const req = backend.expectOne('/manifest.webmanifest');
    expect(req.request.headers.has('X-API-Key')).toBe(false);
    req.flush({});
  });
});
