import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import {
  ButtonComponent,
  ConfirmDialogComponent,
  IconComponent,
  MEDIA,
  ToastService,
  mediaQuery,
} from '@stupa-makers/ui-kit';
import { errorText } from '../../core/api/api.service';
import { ConfigStore } from '../../core/state/config-store.service';
import { AnimationEditorComponent } from '../../features/animation-editor/animation-editor.component';
import { VisualizationComponent } from '../../features/visualization/visualization.component';

/**
 * The editor of the active animation. On a wide screen the live view is next to it, so a
 * saved change shows at once.
 */
@Component({
  selector: 'app-animation-page',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    AnimationEditorComponent,
    ButtonComponent,
    ConfirmDialogComponent,
    IconComponent,
    VisualizationComponent,
  ],
  template: `
    <div class="split" [class.split--two]="wide()">
      @if (wide()) {
        @if (store.config(); as config) {
          <app-visualization class="split__live" [config]="config" />
        }
      }
      <div class="split__main">
        <header class="head">
          <h1 class="page-title">Animation</h1>
          <div class="head__actions">
            @if (store.dirty()) {
              <app-button variant="text" (click)="confirmDiscard.set(true)">Discard</app-button>
            }
            <app-button
              variant="fill"
              [disabled]="!canSave()"
              [loading]="store.saving()"
              (click)="save()"
            >
              <span class="btn-label"><app-icon name="check" [size]="18" /> Save</span>
            </app-button>
          </div>
        </header>
        <section class="card-surface" aria-label="Active animation">
          <app-animation-editor
            [value]="store.draft()"
            [animations]="store.animations()"
            [presets]="store.presets()"
            [strips]="store.config()?.strips ?? []"
            [problems]="store.problems()"
            (changed)="store.draft.set($event)"
          />
        </section>
      </div>
    </div>

    <app-confirm-dialog
      [open]="confirmDiscard()"
      title="Discard the changes?"
      body="The editor goes back to the saved animation."
      confirmLabel="Discard"
      (confirm)="discard()"
      (cancel)="confirmDiscard.set(false)"
    />
  `,
  styles: `
    :host {
      display: flex;
      flex: 1 1 auto;
      flex-direction: column;
      min-height: 0;
    }
    .split {
      display: flex;
      flex: 1 1 auto;
      flex-direction: column;
      gap: var(--space-6);
      width: 100%;
      max-width: var(--layout-max-width);
      margin-inline: auto;
      min-height: 0;
    }
    .split--two {
      flex-direction: row;
      max-width: none;
    }
    .split__live {
      position: sticky;
      top: var(--space-6);
      flex: 1 1 0;
      height: calc(100dvh - 2 * var(--space-6));
      min-width: 0;
    }
    .split__main {
      display: flex;
      flex: 1 1 0;
      flex-direction: column;
      gap: var(--space-5);
      min-width: 0;
    }
    .head {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: var(--space-3);
    }
    .head__actions {
      display: flex;
      gap: var(--space-2);
    }
    .card-surface {
      padding: var(--space-5);
      border-radius: var(--radius-xl);
      background: var(--color-surface-1);
    }
    @media (max-width: 768px) {
      .card-surface {
        padding: var(--space-4);
      }
    }
  `,
})
export class AnimationPage {
  protected readonly store = inject(ConfigStore);
  private readonly toast = inject(ToastService);

  protected readonly wide = mediaQuery(MEDIA.wide);
  protected readonly confirmDiscard = signal(false);

  protected readonly canSave = computed(
    () => this.store.dirty() && this.store.problems().length === 0 && !this.store.saving(),
  );

  protected async save(): Promise<void> {
    try {
      await this.store.save();
      this.toast.success('The animation is saved.');
    } catch (error) {
      this.toast.error(`The animation was not saved: ${errorText(error)}`);
    }
  }

  protected discard(): void {
    this.store.discard();
    this.confirmDiscard.set(false);
  }
}
