import { DOCUMENT } from '@angular/common';
import { Injectable, inject } from '@angular/core';
import { SwUpdate } from '@angular/service-worker';
import { ToastService } from '@stupa-makers/ui-kit';

/**
 * The update of the installed app. When the service worker has a new version in its
 * cache, a toast offers a reload. The service never reloads without the consent of the
 * user, because the editor can hold unsaved changes.
 *
 * Without a service worker (`ng serve`, plain HTTP on the LAN) the service does nothing.
 */
@Injectable({ providedIn: 'root' })
export class SwUpdateService {
  private readonly updates = inject(SwUpdate);
  private readonly toast = inject(ToastService);
  private readonly document = inject(DOCUMENT);

  init(): void {
    if (!this.updates.isEnabled) return;
    this.updates.versionUpdates.subscribe((event) => {
      if (event.type !== 'VERSION_READY') return;
      this.toast.showAction({
        message: 'A new version of the app is ready.',
        action: 'Reload',
        variant: 'info',
        timeout: 0,
        closed: (how) => {
          if (how !== 'action') return;
          void this.updates.activateUpdate().finally(() => this.document.location.reload());
        },
      });
    });
    this.updates.unrecoverable.subscribe(() => this.document.location.reload());
  }
}
