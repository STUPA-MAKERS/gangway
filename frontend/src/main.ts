import { bootstrapApplication } from '@angular/platform-browser';
import { appConfig } from './app/app.config';
import { App } from './app/app';

// iOS Safari sets :active on a touched element only while a touch listener exists on the
// page. The press state of the kit controls is the only feedback of a tap.
document.addEventListener('touchstart', () => undefined, { passive: true });

bootstrapApplication(App, appConfig).catch((err) => console.error(err));
