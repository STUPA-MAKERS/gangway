import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  NgZone,
  computed,
  inject,
  signal,
} from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { ApiService } from '../../core/api/api.service';
import type { AudioData } from '../../core/api/models';

/** The poll interval of the sound analysis. */
const INTERVAL_MS = 100;
/** The time after a beat in which the beat light is on. */
const BEAT_FLASH_S = 0.15;

/**
 * A small live meter of the microphone (`GET /api/data/audio`): the level, the three
 * bands, the spectrum, the beat and the tempo. Use it to tune the audio settings and the
 * audio animations.
 */
@Component({
  selector: 'app-audio-meter',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section class="am" aria-label="Sound">
      @if (audio(); as a) {
        @if (a.capturing) {
          <div class="am__bars">
            @for (band of bands(); track band.label) {
              <div class="am__row">
                <span class="am__name">{{ band.label }}</span>
                <span class="am__track">
                  <span class="am__fill" [style.width.%]="band.value * 100"></span>
                </span>
              </div>
            }
          </div>
          <div class="am__spectrum" aria-hidden="true">
            @for (v of a.spectrum; track $index) {
              <span class="am__band" [style.height.%]="v * 100"></span>
            }
          </div>
          <div class="am__beat">
            <span class="am__light" [class.am__light--on]="beat()" aria-hidden="true"></span>
            <span>{{ a.tempo > 0 ? a.tempo + ' BPM' : 'No tempo' }}</span>
            <span class="am__count">{{ a.beat_count }} beats</span>
          </div>
        } @else {
          <p class="am__off">The microphone gives no sound.</p>
        }
      } @else {
        <p class="am__off">No sound data.</p>
      }
    </section>
  `,
  styles: `
    :host {
      display: block;
    }
    .am {
      display: flex;
      flex-direction: column;
      gap: var(--space-3);
      width: 14rem;
      padding: var(--space-3);
      border-radius: var(--radius-lg);
      background: rgba(0, 0, 0, 0.6);
      color: #e6e8e6;
      font-size: var(--fs-xs);
    }
    .am__bars {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .am__row {
      display: grid;
      grid-template-columns: 3.5rem 1fr;
      align-items: center;
      gap: var(--space-2);
    }
    .am__track {
      height: 6px;
      overflow: hidden;
      border-radius: 3px;
      background: rgba(255, 255, 255, 0.12);
    }
    .am__fill {
      display: block;
      height: 100%;
      border-radius: inherit;
      background: var(--color-accent);
      transition: width 80ms linear;
    }
    .am__spectrum {
      display: flex;
      align-items: flex-end;
      gap: 3px;
      height: 40px;
    }
    .am__band {
      flex: 1 1 0;
      min-height: 2px;
      border-radius: 2px 2px 0 0;
      background: var(--color-accent);
      transition: height 80ms linear;
    }
    .am__beat {
      display: flex;
      align-items: center;
      gap: var(--space-2);
      font-family: var(--font-mono);
    }
    .am__count {
      margin-inline-start: auto;
      color: rgba(255, 255, 255, 0.6);
    }
    .am__light {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.15);
    }
    .am__light--on {
      background: #fff;
      box-shadow: 0 0 10px #fff;
    }
    .am__off {
      margin: 0;
      color: rgba(255, 255, 255, 0.7);
    }
  `,
})
export class AudioMeterComponent {
  private readonly api = inject(ApiService);
  private active = true;

  protected readonly audio = signal<AudioData | null>(null);

  protected readonly bands = computed(() => {
    const a = this.audio();
    if (!a) return [];
    return [
      { label: 'Level', value: clamp01(a.level) },
      { label: 'Bass', value: clamp01(a.bass) },
      { label: 'Mid', value: clamp01(a.mid) },
      { label: 'Treble', value: clamp01(a.treble) },
    ];
  });

  protected readonly beat = computed(() => {
    const since = this.audio()?.since_beat;
    return since !== null && since !== undefined && since < BEAT_FLASH_S;
  });

  constructor() {
    inject(DestroyRef).onDestroy(() => (this.active = false));
    inject(NgZone).runOutsideAngular(() => void this.poll());
  }

  private async poll(): Promise<void> {
    while (this.active) {
      try {
        this.audio.set(await firstValueFrom(this.api.audio()));
      } catch {
        this.audio.set(null);
      }
      await new Promise((resolve) => setTimeout(resolve, INTERVAL_MS));
    }
  }
}

function clamp01(v: number): number {
  return Math.max(0, Math.min(1, v || 0));
}
