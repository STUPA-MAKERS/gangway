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
import { UI_KIT_INTL, uiKitIntlFromLang } from '@stupa-makers/ui-kit';
import { apiKeyInterceptor } from './core/api/api-key.interceptor';
import { SwUpdateService } from './core/pwa/sw-update.service';
import { ThemeService } from './core/theme/theme.service';
import { routes } from './app.routes';

/** The root providers of the app. The UI is in English, so the kit texts are English too. */
export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes, withComponentInputBinding()),
    provideHttpClient(withInterceptors([apiKeyInterceptor])),
    { provide: UI_KIT_INTL, useFactory: () => uiKitIntlFromLang(signal('en')) },
    provideAppInitializer(() => {
      inject(ThemeService).init();
      inject(SwUpdateService).init();
    }),
    // The worker (ngsw-config.json) caches the app shell and the assets, not `/api`. A
    // browser registers it only on HTTPS or on localhost.
    provideServiceWorker('ngsw-worker.js', {
      enabled: !isDevMode(),
      registrationStrategy: 'registerWhenStable:30000',
    }),
  ],
};
