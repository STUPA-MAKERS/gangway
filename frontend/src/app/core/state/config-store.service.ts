import { HttpErrorResponse } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { firstValueFrom, forkJoin } from 'rxjs';
import { ApiKeyService } from '../api/api-key.service';
import { ApiService, errorText } from '../api/api.service';
import type { AnimationConfig, AnimationInfo, GangwayConfig } from '../api/models';
import { clone, validateAnimation } from '../../features/animation-editor/schema';

/**
 * The state of the first load.
 *
 * - `loading`: the requests are open.
 * - `ready`: the config, the animations and the presets are there.
 * - `locked`: the backend refused the API key, or the request had no key.
 * - `offline`: the server does not answer.
 * - `error`: another error. `error()` holds the text.
 */
export type LoadState = 'loading' | 'ready' | 'locked' | 'offline' | 'error';

/**
 * The app state: the config of the backend, the animation draft of the editor, the
 * animation descriptions and the preset names.
 *
 * The draft is a copy of the saved animation. The editor changes the draft only. `save()`
 * sends it to the backend, and `discard()` goes back to the saved animation.
 */
@Injectable({ providedIn: 'root' })
export class ConfigStore {
  private readonly api = inject(ApiService);
  private readonly keys = inject(ApiKeyService);

  readonly state = signal<LoadState>('loading');
  readonly error = signal('');

  readonly config = signal<GangwayConfig | null>(null);
  readonly animations = signal<AnimationInfo[]>([]);
  readonly presets = signal<string[]>([]);
  readonly draft = signal<AnimationConfig>({});
  readonly saving = signal(false);

  /** True if the draft differs from the saved animation. */
  readonly dirty = computed(() => {
    const config = this.config();
    return !!config && JSON.stringify(config.animation) !== JSON.stringify(this.draft());
  });

  /** The problems of the draft. The editor cannot save while there is one. */
  readonly problems = computed(() => validateAnimation(this.draft(), this.animations()));

  /** Loads the config, the animations and the presets. The draft gets the saved animation. */
  async load(): Promise<void> {
    this.state.set('loading');
    this.keys.refused.set(false);
    try {
      const { config, animations, presets } = await firstValueFrom(
        forkJoin({
          config: this.api.config(),
          animations: this.api.animations(),
          presets: this.api.presets(),
        }),
      );
      this.animations.set(animations);
      this.presets.set([...presets].sort((a, b) => a.localeCompare(b)));
      this.applyConfig(config);
      this.state.set('ready');
    } catch (error) {
      this.fail(error);
    }
  }

  /** Reads the config again, for example after a preset load. The draft is reset. */
  async reloadConfig(): Promise<void> {
    this.applyConfig(await firstValueFrom(this.api.config()));
  }

  async reloadPresets(): Promise<void> {
    const presets = await firstValueFrom(this.api.presets());
    this.presets.set([...presets].sort((a, b) => a.localeCompare(b)));
  }

  /** Sends the draft to the backend and reads the saved config back. */
  async save(): Promise<void> {
    const config = this.config();
    if (!config) return;
    this.saving.set(true);
    try {
      await firstValueFrom(this.api.saveConfig({ ...config, animation: this.draft() }));
      await this.reloadConfig();
    } finally {
      this.saving.set(false);
    }
  }

  discard(): void {
    const config = this.config();
    if (config) this.draft.set(clone(config.animation));
  }

  private applyConfig(config: GangwayConfig): void {
    this.config.set(config);
    this.draft.set(clone(config.animation));
  }

  private fail(error: unknown): void {
    if (error instanceof HttpErrorResponse && (error.status === 401 || error.status === 403)) {
      this.state.set('locked');
    } else if (error instanceof HttpErrorResponse && error.status === 0) {
      this.state.set('offline');
    } else {
      this.error.set(errorText(error));
      this.state.set('error');
    }
  }
}
