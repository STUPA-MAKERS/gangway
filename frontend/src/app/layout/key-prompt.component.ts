import { ChangeDetectionStrategy, Component, input, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ButtonComponent, IconComponent, InputComponent } from '@stupa-makers/ui-kit';

/**
 * The prompt for the API key. The shell shows it when the backend refuses a request. On
 * the SSO tunnel nginx adds the key, so the prompt shows on the LAN only.
 */
@Component({
  selector: 'app-key-prompt',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, ButtonComponent, IconComponent, InputComponent],
  template: `
    <section class="kp" aria-labelledby="kp-title">
      <span class="kp__icon" aria-hidden="true"><app-icon name="key" [size]="28" /></span>
      <h1 id="kp-title" class="kp__title">API key</h1>
      <p class="kp__text">The installation needs its API key on this network.</p>
      <form class="kp__form" (ngSubmit)="submit()">
        <app-input
          type="password"
          label="API key"
          name="key"
          [error]="rejected() ? 'The server does not accept this key.' : ''"
          [ngModel]="value()"
          (ngModelChange)="value.set($event)"
        />
        <app-button type="submit" variant="fill" [block]="true" [disabled]="!value().trim()">
          Unlock
        </app-button>
      </form>
    </section>
  `,
  styles: `
    :host {
      display: flex;
      flex: 1 1 auto;
      align-items: center;
      justify-content: center;
      padding: var(--space-6) var(--space-4);
    }
    .kp {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: var(--space-3);
      width: 100%;
      max-width: 24rem;
      padding: var(--space-8) var(--space-6);
      border-radius: var(--radius-2xl);
      background: var(--color-surface-1);
      text-align: center;
    }
    .kp__icon {
      display: grid;
      place-items: center;
      width: 56px;
      height: 56px;
      border-radius: 50%;
      background: var(--color-selected);
      color: var(--color-accent-text);
    }
    .kp__title {
      margin: 0;
      font-size: var(--fs-h1);
      line-height: var(--lh-h1);
    }
    .kp__text {
      margin: 0;
      color: var(--color-text-muted);
    }
    .kp__form {
      display: flex;
      flex-direction: column;
      gap: var(--space-4);
      width: 100%;
      margin-top: var(--space-3);
      text-align: start;
    }
  `,
})
export class KeyPromptComponent {
  /** True if the last key that the user gave was refused. */
  readonly rejected = input(false);
  readonly unlock = output<string>();

  protected readonly value = signal('');

  protected submit(): void {
    const key = this.value().trim();
    if (key) this.unlock.emit(key);
  }
}
