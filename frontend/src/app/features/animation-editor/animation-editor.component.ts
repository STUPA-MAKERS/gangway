import { ChangeDetectionStrategy, Component, computed, input, output } from '@angular/core';
import { NgTemplateOutlet } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
  ButtonComponent,
  IconComponent,
  InputComponent,
  SegmentedComponent,
  type SegmentedOption,
  SelectFieldComponent,
  type SelectFieldOption,
  SwitchComponent,
} from '@stupa-makers/ui-kit';
import type {
  AnimationConfig,
  AnimationInfo,
  ParamInfo,
  Rgbcct,
  Strip,
} from '../../core/api/models';
import { ColorInputComponent } from './color-input.component';
import {
  BLACK,
  type ParamControl,
  type Problem,
  animationName,
  defaultChild,
  isColorValue,
  isPlainObject,
  literalOptions,
  newAnimation,
  paramControl,
} from './schema';

/** One parameter row of the editor. */
interface ParamRow {
  param: ParamInfo;
  control: ParamControl;
  label: string;
  path: string;
}

const SOURCE_OPTIONS: SegmentedOption[] = [
  { value: 'color', label: 'Color' },
  { value: 'animation', label: 'Animation' },
];

/**
 * The editor of one animation and its parameters. The backend schema
 * (`GET /api/animations/`) gives the parameters and their types, so a new animation in the
 * backend needs no change here.
 *
 * The editor is recursive: a parameter that holds an animation shows a nested editor. The
 * editor keeps no state. It emits a new config entry on each change, and the caller sets
 * it as the new `value`.
 */
@Component({
  selector: 'app-animation-editor',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    NgTemplateOutlet,
    FormsModule,
    ButtonComponent,
    IconComponent,
    InputComponent,
    SegmentedComponent,
    SelectFieldComponent,
    SwitchComponent,
    ColorInputComponent,
  ],
  templateUrl: './animation-editor.component.html',
  styleUrl: './animation-editor.component.scss',
})
export class AnimationEditorComponent {
  /** The config entry, for example `{ "static": { "color": {...} } }`. */
  readonly value = input<unknown>(null);
  /** The animations of the backend schema. */
  readonly animations = input<readonly AnimationInfo[]>([]);
  readonly presets = input<readonly string[]>([]);
  readonly strips = input<readonly Strip[]>([]);
  /** The problems of the whole draft (`validateAnimation`). */
  readonly problems = input<readonly Problem[]>([]);
  /** The path of this entry in the draft. The root has the path ''. */
  readonly path = input('');
  /** A nested editor shows a line at its start edge. */
  readonly nested = input(false);
  /** Shows a remove button next to the animation select. */
  readonly removable = input(false);

  readonly changed = output<AnimationConfig>();
  readonly removed = output<void>();

  protected readonly sourceOptions = SOURCE_OPTIONS;

  protected readonly name = computed(() => animationName(this.value()));

  protected readonly params = computed<Record<string, unknown>>(() => {
    const value = this.value();
    const name = this.name();
    const params = isPlainObject(value) ? value[name] : null;
    return isPlainObject(params) ? params : {};
  });

  protected readonly info = computed(() => this.animations().find((a) => a.name === this.name()));

  protected readonly options = computed<SelectFieldOption[]>(() =>
    this.animations().map((a) => ({ value: a.name, label: a.title || a.name })),
  );

  protected readonly presetOptions = computed<SelectFieldOption[]>(() =>
    this.presets().map((p) => ({ value: p, label: p })),
  );

  protected readonly stripOptions = computed<SelectFieldOption[]>(() =>
    this.strips().map((s, i) => ({ value: String(i), label: `Strip ${i + 1} (${s.index})` })),
  );

  protected readonly rows = computed<ParamRow[]>(() => {
    const name = this.name();
    const hasStrips = this.strips().length > 0;
    return (this.info()?.params ?? []).map((param) => ({
      param,
      control: paramControl(param, name, hasStrips),
      label: humanize(param.name),
      path: join(this.path(), name, param.name),
    }));
  });

  /** The problem of a field, or ''. */
  protected problemAt(path: string): string {
    return this.problems().find((p) => p.path === path)?.message ?? '';
  }

  protected selectAnimation(name: string): void {
    if (!name || name === this.name()) return;
    this.changed.emit(newAnimation(name, this.animations()));
  }

  /** Sets a parameter. `undefined` removes it, so the default of the backend applies. */
  protected setParam(param: string, value: unknown): void {
    const params = { ...this.params() };
    if (value === undefined) delete params[param];
    else params[param] = value;
    this.changed.emit({ [this.name()]: params });
  }

  protected valueOf(row: ParamRow): unknown {
    return this.params()[row.param.name];
  }

  protected listOf(row: ParamRow): unknown[] {
    const value = this.valueOf(row);
    return Array.isArray(value) ? value : [];
  }

  protected setItem(row: ParamRow, index: number, item: unknown): void {
    const list = [...this.listOf(row)];
    list[index] = item;
    this.setParam(row.param.name, list);
  }

  protected removeItem(row: ParamRow, index: number): void {
    this.setParam(
      row.param.name,
      this.listOf(row).filter((_, i) => i !== index),
    );
  }

  protected addAnimation(row: ParamRow): void {
    this.setParam(row.param.name, [...this.listOf(row), defaultChild(this.animations())]);
  }

  protected addColor(row: ParamRow): void {
    this.setParam(row.param.name, [...this.listOf(row), { ...BLACK }]);
  }

  protected addAssignment(row: ParamRow): void {
    this.setParam(row.param.name, [
      ...this.listOf(row),
      { strip_assignment: { strip: 0, animation: defaultChild(this.animations()) } },
    ]);
  }

  protected assignmentOf(item: unknown): { strip: unknown; animation: unknown } {
    const sa = isPlainObject(item) ? item['strip_assignment'] : null;
    return isPlainObject(sa)
      ? { strip: sa['strip'], animation: sa['animation'] }
      : { strip: 0, animation: undefined };
  }

  protected setAssignment(row: ParamRow, index: number, field: 'strip' | 'animation', value: unknown): void {
    const current = this.listOf(row)[index];
    const sa = isPlainObject(current) && isPlainObject(current['strip_assignment'])
      ? current['strip_assignment']
      : {};
    this.setItem(row, index, { strip_assignment: { ...sa, [field]: value } });
  }

  // --- a color or a nested animation ------------------------------------------------

  protected setParamFn(row: ParamRow): (value: unknown) => void {
    return (value) => this.setParam(row.param.name, value);
  }

  protected setAssignmentFn(row: ParamRow, index: number): (value: unknown) => void {
    return (value) => this.setAssignment(row, index, 'animation', value);
  }

  protected sourceOf(value: unknown): 'color' | 'animation' {
    return isColorValue(value) || value === undefined || value === null ? 'color' : 'animation';
  }

  /** The value for a change of the source: white, or the first animation. */
  protected switchSource(source: string | null): unknown {
    return source === 'animation'
      ? defaultChild(this.animations())
      : ({ r: 255, g: 255, b: 255, cw: 0, ww: 0 } satisfies Rgbcct);
  }

  // --- single values -----------------------------------------------------------------

  protected text(value: unknown): string {
    return value === undefined || value === null ? '' : String(value);
  }

  protected defaultText(row: ParamRow): string {
    const d = row.param.default;
    return d === undefined || d === null || typeof d === 'object' ? '' : String(d);
  }

  protected literalOptions(row: ParamRow): SegmentedOption[] {
    return literalOptions(row.param.type).map((o) => ({ value: o, label: o }));
  }

  /** The literal value, or the default while the config holds none. */
  protected literalValue(row: ParamRow): string {
    return this.text(this.valueOf(row) ?? row.param.default);
  }

  protected boolValue(row: ParamRow): boolean {
    return Boolean(this.valueOf(row) ?? row.param.default);
  }

  protected setNumber(row: ParamRow, text: string): void {
    if (text.trim() === '') {
      this.setParam(row.param.name, undefined);
      return;
    }
    const n = row.param.type.name === 'int' ? parseInt(text, 10) : parseFloat(text);
    this.setParam(row.param.name, Number.isFinite(n) ? n : text);
  }

  /** Moves a number into its limits when the field loses the focus. */
  protected clampNumber(row: ParamRow): void {
    const value = this.valueOf(row);
    if (typeof value !== 'number') return;
    const { min, max } = row.param;
    let n = value;
    if (max !== null && max !== undefined && n > max) n = max;
    if (min !== null && min !== undefined && n < min) n = min;
    if (n !== value) this.setParam(row.param.name, n);
  }

  protected rangeHint(row: ParamRow): string {
    const { min, max } = row.param;
    if (min !== null && max !== null) return `${min} to ${max}`;
    if (min !== null) return `Minimum ${min}`;
    if (max !== null) return `Maximum ${max}`;
    return '';
  }

  protected stripValue(row: ParamRow): string {
    return this.text(this.valueOf(row) ?? 0);
  }
}

function join(...parts: string[]): string {
  return parts.filter((p) => p !== '').join('.');
}

/** `max_radius` → `Max radius`. */
export function humanize(name: string): string {
  const text = name.replace(/_/g, ' ');
  return text.charAt(0).toUpperCase() + text.slice(1);
}
