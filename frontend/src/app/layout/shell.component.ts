import {
  ChangeDetectionStrategy,
  Component,
  HostListener,
  computed,
  inject,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import {
  ActivatedRoute,
  NavigationEnd,
  Router,
  RouterLink,
  RouterLinkActive,
  RouterOutlet,
} from '@angular/router';
import { filter } from 'rxjs';
import {
  ButtonComponent,
  EmptyStateComponent,
  IconComponent,
  type IconName,
  MEDIA,
  ToastComponent,
  mediaQuery,
} from '@stupa-makers/ui-kit';
import { ApiKeyService } from '../core/api/api-key.service';
import { ConfigStore } from '../core/state/config-store.service';
import { ThemeService } from '../core/theme/theme.service';
import { KeyPromptComponent } from './key-prompt.component';

interface NavItem {
  path: string;
  label: string;
  icon: IconName;
}

/** The areas of the app, in the order of the rail and the bottom bar. */
export const NAV_ITEMS: readonly NavItem[] = [
  { path: '/live', label: 'Live', icon: 'monitor' },
  { path: '/animation', label: 'Animation', icon: 'palette' },
  { path: '/presets', label: 'Presets', icon: 'list' },
];

/**
 * The frame of the app: the navigation rail at the start edge, or the bottom bar on a
 * phone, around the router outlet.
 *
 * The page shows only after the first load. Before that the frame shows the load state:
 * a spinner, the prompt for the API key, or the offline or error state with a retry.
 */
@Component({
  selector: 'app-shell',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    ButtonComponent,
    EmptyStateComponent,
    IconComponent,
    ToastComponent,
    KeyPromptComponent,
  ],
  templateUrl: './shell.component.html',
  styleUrl: './shell.component.scss',
})
export class ShellComponent {
  protected readonly store = inject(ConfigStore);
  protected readonly keys = inject(ApiKeyService);
  protected readonly theme = inject(ThemeService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  protected readonly items = NAV_ITEMS;
  protected readonly phone = mediaQuery(MEDIA.phone);

  /** The page fills the free height (route data `fill`). */
  protected readonly fill = signal(false);

  /** True after the user gave a key that the backend refused. */
  protected readonly rejected = signal(false);

  protected readonly locked = computed(
    () => this.store.state() === 'locked' || this.keys.refused(),
  );

  constructor() {
    this.router.events
      .pipe(
        filter((e) => e instanceof NavigationEnd),
        takeUntilDestroyed(),
      )
      .subscribe(() => {
        let r = this.route.firstChild;
        let fill = false;
        while (r) {
          fill = r.snapshot.data['fill'] === true || fill;
          r = r.firstChild;
        }
        this.fill.set(fill);
      });
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
