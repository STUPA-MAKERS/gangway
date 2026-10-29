import { HttpErrorResponse, type HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';
import { ApiKeyService } from './api-key.service';

/**
 * Adds the stored API key to each request to `/api/`. A request with no stored key goes
 * out with no header, so nginx can add the key on the SSO tunnel. A 401 or 403 answer
 * sets `ApiKeyService.refused`, and the shell asks for a key.
 */
export const apiKeyInterceptor: HttpInterceptorFn = (req, next) => {
  if (!req.url.startsWith('/api/')) return next(req);
  const keys = inject(ApiKeyService);
  const key = keys.key();
  const request = key ? req.clone({ setHeaders: { 'X-API-Key': key } }) : req;
  return next(request).pipe(
    catchError((error: unknown) => {
      if (error instanceof HttpErrorResponse && (error.status === 401 || error.status === 403)) {
        keys.refused.set(true);
      }
      return throwError(() => error);
    }),
  );
};
