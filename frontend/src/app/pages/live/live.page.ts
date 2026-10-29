import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { ConfigStore } from '../../core/state/config-store.service';
import { VisualizationComponent } from '../../features/visualization/visualization.component';

/** The live view of the installation. It fills the free height of the page. */
@Component({
  selector: 'app-live-page',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [VisualizationComponent],
  template: `
    @if (store.config(); as config) {
      <app-visualization [config]="config" />
    }
  `,
  styles: `
    :host {
      display: flex;
      flex: 1 1 auto;
      flex-direction: column;
      min-height: 0;
    }
  `,
})
export class LivePage {
  protected readonly store = inject(ConfigStore);
}
