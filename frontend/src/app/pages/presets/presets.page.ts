import {
  ChangeDetectionStrategy,
  Component,
  computed,
  effect,
  inject,
  input,
  signal,
  untracked,
  viewChild,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import {
  ButtonComponent,
  ConfirmDialogComponent,
  DialogComponent,
  EmptyStateComponent,
  IconComponent,
  InputComponent,
  ListDetailLayoutComponent,
  MEDIA,
  ListItemComponent,
  RowMenuComponent,
  type RowMenuItem,
  type RowMenuSection,
  ScrollFadeDirective,
  SearchPillComponent,
  SheetBarComponent,
  SheetBarTitleDirective,
  StickyBarComponent,
  ToastService,
  mediaQuery,
} from '@stupa-makers/ui-kit';
import { ApiService, errorText } from '../../core/api/api.service';
import type { AnimationConfig } from '../../core/api/models';
import { ConfigStore } from '../../core/state/config-store.service';
import { AnimationEditorComponent } from '../../features/animation-editor/animation-editor.component';
import { animationName, validateAnimation } from '../../features/animation-editor/schema';

/** The characters that the backend accepts in a preset name (`validate_preset_name`). */
export const PRESET_NAME = /^[a-zA-Z0-9 \-_]+$/;

const ROW_MENU: RowMenuSection[] = [
  {
    items: [
      { id: 'load', label: 'Load', icon: 'play' },
      { id: 'rename', label: 'Rename', icon: 'tag' },
    ],
  },
  { items: [{ id: 'delete', label: 'Delete', icon: 'trash', danger: true }] },
];

const SHEET_MENU: RowMenuSection[] = [
  { items: [{ id: 'rename', label: 'Rename', icon: 'tag' }] },
  { items: [{ id: 'delete', label: 'Delete', icon: 'trash', danger: true }] },
];

/**
 * The presets as a list with a detail sheet beside it (`app-list-detail`).
 *
 * The list column has a header, a search bar and the presets. The second line of a row
 * names the outer animation of the preset. The floating button of the list saves the
 * animation of the editor on the animation page as a new preset.
 *
 * A row opens the preset at `/presets/:name`. The sheet has the name and the editor. Load floats at the bottom end, and Reset and Save join it
 * while the editor has changes.
 *
 * Wide, the list and the sheet sit side by side. Otherwise one shows at a time, and the
 * bar of the layout leads back to the list.
 */
@Component({
  selector: 'app-presets-page',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    FormsModule,
    AnimationEditorComponent,
    ButtonComponent,
    ConfirmDialogComponent,
    DialogComponent,
    EmptyStateComponent,
    IconComponent,
    InputComponent,
    ListDetailLayoutComponent,
    ListItemComponent,
    RowMenuComponent,
    ScrollFadeDirective,
    SearchPillComponent,
    SheetBarComponent,
    SheetBarTitleDirective,
    StickyBarComponent,
  ],
  templateUrl: './presets.page.html',
  styleUrl: './presets.page.scss',
})
export class PresetsPage {
  private readonly api = inject(ApiService);
  private readonly toast = inject(ToastService);
  private readonly router = inject(Router);
  protected readonly store = inject(ConfigStore);

  /** The open preset, from the route `/presets/:name`. */
  readonly name = input<string | undefined>();

  protected readonly rowMenu = ROW_MENU;
  protected readonly sheetMenu = SHEET_MENU;
  protected readonly busy = signal(false);

  protected readonly phone = mediaQuery(MEDIA.phone);
  private readonly layout = viewChild(ListDetailLayoutComponent);
  /** The list and the sheet sit side by side. */
  protected readonly split = computed(() => this.layout()?.collapsed() === false);

  protected readonly selected = computed(() => this.name() ?? null);

  /** The search text, and the presets whose name holds it, without regard to case. */
  protected readonly search = signal('');
  protected readonly filtered = computed(() => {
    const query = this.search().trim().toLowerCase();
    const names = this.store.presets();
    return query ? names.filter((name) => name.toLowerCase().includes(query)) : names;
  });

  /** The title of the outer animation of each preset, for the second line of its row. */
  private readonly animations = signal<ReadonlyMap<string, AnimationConfig>>(new Map());
  protected readonly summaries = computed(() => {
    const infos = this.store.animations();
    const titles = new Map<string, string>();
    for (const [name, config] of this.animations()) {
      const key = animationName(config);
      titles.set(name, key ? (infos.find((a) => a.name === key)?.title ?? key) : 'Color');
    }
    return titles;
  });

  /** The saved animation of the open preset, and the draft in its editor. */
  private readonly saved = signal<AnimationConfig | null>(null);
  protected readonly draft = signal<AnimationConfig>({});
  protected readonly loading = signal(false);
  protected readonly problems = computed(() =>
    validateAnimation(this.draft(), this.store.animations()),
  );
  protected readonly dirty = computed(() => {
    const saved = this.saved();
    return saved !== null && JSON.stringify(saved) !== JSON.stringify(this.draft());
  });
  protected readonly canSave = computed(
    () => this.dirty() && this.problems().length === 0 && !this.busy(),
  );
  protected readonly confirmReset = signal(false);

  protected readonly creating = signal(false);
  protected readonly newName = signal('');
  protected readonly newNameError = computed(() => nameError(this.newName()));

  protected readonly renaming = signal<string | null>(null);
  protected readonly renameTo = signal('');
  protected readonly renameError = computed(() => nameError(this.renameTo()));

  protected readonly deleting = signal<string | null>(null);

  constructor() {
    effect(() => {
      const name = this.selected();
      untracked(() => void this.open(name));
    });
    effect(() => {
      const names = this.store.presets();
      untracked(() => void this.readAll(names));
    });
  }

  protected close(): void {
    void this.router.navigate(['/presets']);
  }

  protected startCreate(): void {
    this.newName.set('');
    this.creating.set(true);
  }

  /** Saves the animation of the editor on the animation page as a new preset. */
  protected async create(): Promise<void> {
    const name = this.newName().trim();
    if (!name || this.newNameError()) return;
    await this.run(async () => {
      await firstValueFrom(this.api.savePreset(name, this.store.draft()));
      this.creating.set(false);
      await this.store.reloadPresets();
      this.toast.success(`The preset "${name}" is saved.`);
      await this.router.navigate(['/presets', name]);
    }, 'The preset was not saved');
  }

  protected async load(name: string): Promise<void> {
    await this.run(async () => {
      await firstValueFrom(this.api.loadPreset(name));
      await this.store.reloadConfig();
      this.toast.success(`The preset "${name}" is active.`);
    }, 'The preset was not loaded');
  }

  protected async save(): Promise<void> {
    const name = this.selected();
    if (!name || !this.canSave()) return;
    const draft = this.draft();
    await this.run(async () => {
      await firstValueFrom(this.api.savePreset(name, draft));
      this.saved.set(draft);
      this.animations.update((all) => new Map(all).set(name, draft));
      this.toast.success(`The preset "${name}" is saved.`);
    }, 'The preset was not saved');
  }

  protected reset(): void {
    const saved = this.saved();
    if (saved) this.draft.set(saved);
    this.confirmReset.set(false);
  }

  protected startRename(name: string): void {
    this.renameTo.set(name);
    this.renaming.set(name);
  }

  protected async rename(): Promise<void> {
    const name = this.renaming();
    const to = this.renameTo().trim();
    if (!name || !to || this.renameError()) return;
    if (to === name) {
      this.renaming.set(null);
      return;
    }
    await this.run(async () => {
      await firstValueFrom(this.api.renamePreset(name, to));
      this.renaming.set(null);
      await this.store.reloadPresets();
      this.toast.success(`The preset is renamed to "${to}".`);
      if (this.selected() === name) await this.router.navigate(['/presets', to]);
    }, 'The preset was not renamed');
  }

  protected async remove(): Promise<void> {
    const name = this.deleting();
    if (!name) return;
    await this.run(async () => {
      await firstValueFrom(this.api.deletePreset(name));
      this.deleting.set(null);
      await this.store.reloadPresets();
      this.toast.success(`The preset "${name}" is deleted.`);
      if (this.selected() === name) this.close();
    }, 'The preset was not deleted');
  }

  protected onMenu(name: string, item: RowMenuItem): void {
    if (item.id === 'load') void this.load(name);
    else if (item.id === 'rename') this.startRename(name);
    else if (item.id === 'delete') this.deleting.set(name);
  }

  /** Reads the preset into the editor. A preset with changes loses them. */
  private async open(name: string | null): Promise<void> {
    this.saved.set(null);
    this.draft.set({});
    if (name === null) return;
    this.loading.set(true);
    try {
      const preset = await firstValueFrom(this.api.preset(name));
      if (this.selected() !== name) return;
      this.saved.set(preset.animation);
      this.draft.set(preset.animation);
    } catch (error) {
      this.toast.error(`The preset was not read: ${errorText(error)}`);
    } finally {
      this.loading.set(false);
    }
  }

  /** Reads all presets for the second lines of the rows. A preset that fails has none. */
  private async readAll(names: readonly string[]): Promise<void> {
    const read = await Promise.all(
      names.map(async (name) => {
        try {
          return [name, (await firstValueFrom(this.api.preset(name))).animation] as const;
        } catch {
          return null;
        }
      }),
    );
    this.animations.set(new Map(read.filter((entry) => entry !== null)));
  }

  private async run(action: () => Promise<void>, failure: string): Promise<void> {
    this.busy.set(true);
    try {
      await action();
    } catch (error) {
      this.toast.error(`${failure}: ${errorText(error)}`);
    } finally {
      this.busy.set(false);
    }
  }
}

/** The error text for a preset name, or '' if the name is empty or valid. */
export function nameError(name: string): string {
  const value = name.trim();
  if (!value || PRESET_NAME.test(value)) return '';
  return 'Use only letters, digits, spaces, hyphens and underscores.';
}
