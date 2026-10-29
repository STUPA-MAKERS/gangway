import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { firstValueFrom } from 'rxjs';
import {
  ButtonComponent,
  ConfirmDialogComponent,
  DialogComponent,
  EmptyStateComponent,
  IconComponent,
  InputComponent,
  ListItemComponent,
  RowMenuComponent,
  type RowMenuItem,
  type RowMenuSection,
  ToastService,
} from '@stupa-makers/ui-kit';
import { ApiService, errorText } from '../../core/api/api.service';
import type { AnimationConfig } from '../../core/api/models';
import { ConfigStore } from '../../core/state/config-store.service';
import { AnimationEditorComponent } from '../../features/animation-editor/animation-editor.component';
import { validateAnimation } from '../../features/animation-editor/schema';

/** The characters that the backend accepts in a preset name (`validate_preset_name`). */
export const PRESET_NAME = /^[a-zA-Z0-9 \-_]+$/;

const MENU: RowMenuSection[] = [
  {
    items: [
      { id: 'edit', label: 'Edit', icon: 'edit' },
      { id: 'rename', label: 'Rename', icon: 'tag' },
    ],
  },
  { items: [{ id: 'delete', label: 'Delete', icon: 'trash', danger: true }] },
];

/**
 * The presets: save the current animation as a preset, and load, edit, rename or delete
 * a preset.
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
    ListItemComponent,
    RowMenuComponent,
  ],
  templateUrl: './presets.page.html',
  styleUrl: './presets.page.scss',
})
export class PresetsPage {
  private readonly api = inject(ApiService);
  private readonly toast = inject(ToastService);
  protected readonly store = inject(ConfigStore);

  protected readonly menu = MENU;
  protected readonly busy = signal(false);

  protected readonly newName = signal('');
  protected readonly newNameError = computed(() => nameError(this.newName()));

  /** The preset in the edit dialog, and its draft. */
  protected readonly editing = signal<string | null>(null);
  protected readonly editDraft = signal<AnimationConfig>({});
  protected readonly editProblems = computed(() =>
    validateAnimation(this.editDraft(), this.store.animations()),
  );

  protected readonly renaming = signal<string | null>(null);
  protected readonly renameTo = signal('');
  protected readonly renameError = computed(() => nameError(this.renameTo()));

  protected readonly deleting = signal<string | null>(null);

  /** Saves the animation of the editor, with its unsaved changes, as a new preset. */
  protected async saveCurrent(): Promise<void> {
    const name = this.newName().trim();
    if (!name || this.newNameError()) return;
    await this.run(async () => {
      await firstValueFrom(this.api.savePreset(name, this.store.draft()));
      this.newName.set('');
      await this.store.reloadPresets();
      this.toast.success(`The preset "${name}" is saved.`);
    }, 'The preset was not saved');
  }

  protected async load(name: string): Promise<void> {
    await this.run(async () => {
      await firstValueFrom(this.api.loadPreset(name));
      await this.store.reloadConfig();
      this.toast.success(`The preset "${name}" is active.`);
    }, 'The preset was not loaded');
  }

  protected async edit(name: string): Promise<void> {
    await this.run(async () => {
      const preset = await firstValueFrom(this.api.preset(name));
      this.editDraft.set(preset.animation);
      this.editing.set(name);
    }, 'The preset was not read');
  }

  protected async saveEdit(): Promise<void> {
    const name = this.editing();
    if (!name || this.editProblems().length) return;
    await this.run(async () => {
      await firstValueFrom(this.api.savePreset(name, this.editDraft()));
      this.editing.set(null);
      this.toast.success(`The preset "${name}" is updated.`);
    }, 'The preset was not updated');
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
    }, 'The preset was not deleted');
  }

  protected onMenu(name: string, item: RowMenuItem): void {
    if (item.id === 'edit') void this.edit(name);
    else if (item.id === 'rename') this.startRename(name);
    else if (item.id === 'delete') this.deleting.set(name);
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
