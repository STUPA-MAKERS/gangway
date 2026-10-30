import {
  ChangeDetectionStrategy,
  Component,
  HostListener,
  computed,
  inject,
  signal,
} from '@angular/core';
import { ButtonComponent, EmptyStateComponent, ThemeService } from '@stupa-makers/ui-kit';
import {
  BarButtonComponent,
  RailButtonComponent,
  ShellComponent,
  type ShellNavItem,
} from '@stupa-makers/ui-kit/shell';
import { ApiKeyService } from './core/api/api-key.service';
import { ConfigStore } from './core/state/config-store.service';
import { KeyPromptComponent } from './layout/key-prompt.component';

/** The areas of the app, in the order of the rail and the bottom bar. */
export const NAV_ITEMS: readonly ShellNavItem[] = [
  { key: 'live', path: '/live', label: 'Live', icon: 'monitor', place: 'main' },
  { key: 'animation', path: '/animation', label: 'Animation', icon: 'palette', place: 'main' },
  { key: 'presets', path: '/presets', label: 'Presets', icon: 'list', place: 'main' },
  { key: 'stats', path: '/stats', label: 'Statistics', icon: 'pie', place: 'main' },
];

/**
 * The root component: the frame of the kit (`app-shell`) with the navigation rail, or the
 * bottom bar on a phone, around the router outlet. The theme switch is the last entry of
 * the rail and of the bar.
 *
 * The page shows only after the first load. Before that the main area shows the load
 * state: a spinner, the prompt for the API key, or the offline or error state with a
 * retry.
 */
@Component({
  selector: 'app-root',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    ShellComponent,
    RailButtonComponent,
    BarButtonComponent,
    ButtonComponent,
    EmptyStateComponent,
    KeyPromptComponent,
  ],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {
  protected readonly store = inject(ConfigStore);
  protected readonly keys = inject(ApiKeyService);
  protected readonly theme = inject(ThemeService);

  protected readonly nav = NAV_ITEMS;
  protected readonly barKeys = NAV_ITEMS.map((item) => item.key);
  protected readonly brand = { home: '/live', label: 'Gangway', mark: 'favicon.svg' };

  /** True after the user gave a key that the backend refused. */
  protected readonly rejected = signal(false);

  protected readonly locked = computed(
    () => this.store.state() === 'locked' || this.keys.refused(),
  );

  /** The first load is done and the key is accepted, so the router outlet shows. */
  protected readonly ready = computed(() => !this.locked() && this.store.state() === 'ready');

  constructor() {
    void this.store.load();
  }

  protected async unlock(key: string): Promise<void> {
    this.keys.set(key);
    await this.store.load();
    this.rejected.set(this.store.state() === 'locked');
  }

  protected retry(): void {
    void this.store.load();
  }

  /** The browser asks before it closes a page with unsaved changes. */
  @HostListener('window:beforeunload', ['$event'])
  protected onBeforeUnload(event: BeforeUnloadEvent): void {
    if (this.store.dirty()) event.preventDefault();
  }
}
