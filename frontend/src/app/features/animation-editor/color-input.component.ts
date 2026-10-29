import { ChangeDetectionStrategy, Component, computed, input, output } from '@angular/core';
import type { Rgbcct } from '../../core/api/models';
import { BLACK, CHANNELS, clampChannel, cssColor, hexColor, isPlainObject, parseHex } from './schema';

const CHANNEL_LABELS: Record<(typeof CHANNELS)[number], string> = {
  r: 'Red',
  g: 'Green',
  b: 'Blue',
  cw: 'Cold white',
  ww: 'Warm white',
};

/**
 * An RGBCCT color: a swatch that opens the color picker of the browser for the RGB part,
 * and one field for each of the five channels (0 to 255).
 */
@Component({
  selector: 'app-color-input',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="ci">
      <label class="ci__swatch" [style.background-color]="css()">
        <input
          type="color"
          class="ci__picker"
          [value]="hex()"
          [attr.aria-label]="label() ? label() + ': color picker' : 'Color picker'"
          (input)="pick($event)"
        />
      </label>
      <div class="ci__channels">
        @for (ch of channels; track ch) {
          <label class="ci__ch" [attr.data-ch]="ch">
            <span class="ci__name" aria-hidden="true">{{ ch }}</span>
            <input
              class="ci__field"
              type="number"
              inputmode="numeric"
              min="0"
              max="255"
              step="1"
              [value]="color()[ch]"
              [attr.aria-label]="channelLabels[ch]"
              (change)="setChannel(ch, $event)"
            />
          </label>
        }
      </div>
    </div>
  `,
  styles: `
    @use 'field' as f;

    .ci {
      display: flex;
      align-items: flex-end;
      gap: var(--space-3);
      min-width: 0;
    }
    .ci__swatch {
      position: relative;
      flex: none;
      width: 48px;
      height: 48px;
      border-radius: var(--radius-field);
      box-shadow: inset 0 0 0 1px var(--color-border);
      cursor: pointer;
    }
    .ci__swatch:focus-within {
      box-shadow: inset 0 0 0 2px var(--color-focus-ring);
    }
    .ci__picker {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      opacity: 0;
      cursor: pointer;
    }
    .ci__channels {
      display: grid;
      flex: 1 1 auto;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: var(--space-2);
      min-width: 0;
    }
    .ci__ch {
      display: flex;
      flex-direction: column;
      gap: 2px;
      min-width: 0;
    }
    .ci__name {
      padding-inline: var(--space-1);
      font-size: var(--fs-xs);
      font-weight: var(--fw-semibold);
      text-transform: uppercase;
      color: var(--color-text-subtle);
    }
    .ci__ch[data-ch='r'] .ci__name {
      color: #e5484d;
    }
    .ci__ch[data-ch='g'] .ci__name {
      color: #30a46c;
    }
    .ci__ch[data-ch='b'] .ci__name {
      color: #3e63dd;
    }
    .ci__field {
      @include f.control;
      height: 36px;
      padding: 0 var(--space-1);
      text-align: center;
      font-variant-numeric: tabular-nums;
      background: var(--color-surface-sunken);
    }
    .ci__field:focus-visible {
      box-shadow: inset 0 0 0 2px var(--color-focus-ring);
    }
  `,
})
export class ColorInputComponent {
  /** The color. A missing value or a missing channel counts as 0. */
  readonly value = input<unknown>(null);
  /** The name of the parameter, for the accessible names. */
  readonly label = input('');
  readonly changed = output<Rgbcct>();

  protected readonly channels = CHANNELS;
  protected readonly channelLabels = CHANNEL_LABELS;

  protected readonly color = computed<Rgbcct>(() => {
    const v = this.value();
    if (!isPlainObject(v)) return { ...BLACK };
    return {
      r: clampChannel(v['r'] ?? 0),
      g: clampChannel(v['g'] ?? 0),
      b: clampChannel(v['b'] ?? 0),
      cw: clampChannel(v['cw'] ?? 0),
      ww: clampChannel(v['ww'] ?? 0),
    };
  });
  protected readonly css = computed(() => cssColor(this.color()));
  protected readonly hex = computed(() => hexColor(this.color()));

  protected pick(event: Event): void {
    const rgb = parseHex((event.target as HTMLInputElement).value);
    if (rgb) this.changed.emit({ ...this.color(), ...rgb });
  }

  protected setChannel(channel: (typeof CHANNELS)[number], event: Event): void {
    const field = event.target as HTMLInputElement;
    const value = clampChannel(field.value);
    field.value = String(value);
    this.changed.emit({ ...this.color(), [channel]: value });
  }
}
