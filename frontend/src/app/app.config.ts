import {
  type ApplicationConfig,
  inject,
  isDevMode,
  provideAppInitializer,
  provideBrowserGlobalErrorListeners,
  provideZoneChangeDetection,
  signal,
} from '@angular/core';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideRouter, withComponentInputBinding } from '@angular/router';
import { provideServiceWorker } from '@angular/service-worker';
import { ThemeService, provideUiKit } from '@stupa-makers/ui-kit';
import { OfflineService, SwUpdateService } from '@stupa-makers/ui-kit/pwa';
import { apiKeyInterceptor } from './core/api/api-key.interceptor';
import { routes } from './app.routes';

/**
 * The root providers of the app. The UI is in English, so the kit texts are English too.
 * The theme keeps the storage key of the former app service, so a saved theme stays. The
 * app has one manifest for both themes, so the theme service leaves its link as it is.
 */
export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes, withComponentInputBinding()),
    provideHttpClient(withInterceptors([apiKeyInterceptor])),
    provideUiKit({ lang: signal('en'), theme: { storageKey: 'gangway.theme', manifest: null } }),
    provideAppInitializer(() => {
      inject(ThemeService).init();
      inject(SwUpdateService).init();
      inject(OfflineService).init();
    }),
    // The worker (ngsw-config.json) caches the app shell and the assets, not `/api`. A
    // browser registers it only on HTTPS or on localhost.
    provideServiceWorker('ngsw-worker.js', {
      enabled: !isDevMode(),
      registrationStrategy: 'registerWhenStable:30000',
    }),
  ],
};
