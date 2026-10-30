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

    @if (store.dirty() || store.saving()) {
      <div class="fabs">
        <app-button
          class="fab-reset"
          variant="fab"
          [iconOnly]="true"
          ariaLabel="Reset"
          [disabled]="store.saving()"
          (click)="confirmDiscard.set(true)"
        >
          <app-icon name="reset" />
        </app-button>
        <app-button
          variant="fab"
          [iconOnly]="true"
          ariaLabel="Save"
          [disabled]="!canSave() && !store.saving()"
          [loading]="store.saving()"
          (click)="save()"
        >
          <app-icon name="check" />
        </app-button>
      </div>
    }

    <app-confirm-dialog
      [open]="confirmDiscard()"
      title="Reset the changes?"
      body="The editor goes back to the saved animation."
      confirmLabel="Reset"
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
    .split__main {
      padding-bottom: calc(56px + var(--space-6));
    }
    .fabs {
      position: fixed;
      right: var(--space-6);
      bottom: var(--space-6);
      z-index: var(--z-sticky);
      display: flex;
      gap: var(--space-3);
      animation: fabs-in var(--motion-fast) var(--ease-enter);
    }
    :host-context(.frame--phone) .fabs {
      right: var(--space-4);
      bottom: calc(var(--bottom-bar-height) + env(safe-area-inset-bottom) + var(--space-4));
    }
    .fab-reset ::ng-deep .btn--fab {
      background: var(--color-surface-3);
      color: var(--color-text);
    }
    @keyframes fabs-in {
      from {
        opacity: 0;
        transform: translateY(var(--space-3));
      }
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
