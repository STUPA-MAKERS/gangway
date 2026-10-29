/**
 * Pure functions that read the animation schema of the backend (`GET /api/animations/`).
 * The editor builds its controls from them.
 */
import type { AnimationConfig, AnimationInfo, ParamInfo, Rgbcct, TypeInfo } from '../../core/api/models';

/**
 * The control for one parameter.
 *
 * - `animation-list`: a list of nested animations.
 * - `strip-assignments`: the list of the `by_strip` animation, a strip and an animation each.
 * - `color-list`: a list of colors.
 * - `color-or-animation`: a color or a nested animation.
 * - `animation`: a nested animation.
 * - `preset`: the name of a preset.
 * - `literal`: one of fixed strings.
 * - `color`, `bool`, `time`, `strip`, `number`, `text`: one value.
 */
export type ParamControl =
  | 'animation-list'
  | 'strip-assignments'
  | 'color-list'
  | 'color-or-animation'
  | 'animation'
  | 'preset'
  | 'literal'
  | 'color'
  | 'bool'
  | 'time'
  | 'strip'
  | 'number'
  | 'text';

/** `inspect.Parameter.VAR_POSITIONAL`: a parameter that takes a list of animations. */
const VAR_POSITIONAL = 2;

/** A black color with no white. */
export const BLACK: Rgbcct = { r: 0, g: 0, b: 0, cw: 0, ww: 0 };

/** The five channels of an RGBCCT color, in display order. */
export const CHANNELS = ['r', 'g', 'b', 'cw', 'ww'] as const;

/** Finds a type with the name in the type tree, depth first. */
export function findType(type: TypeInfo | null | undefined, name: string): TypeInfo | null {
  if (!type) return null;
  if (type.name === name) return type;
  for (const arg of type.args ?? []) {
    const found = findType(arg, name);
    if (found) return found;
  }
  return null;
}

export function isColorType(type: TypeInfo | null | undefined): boolean {
  return !!findType(type, 'RGBCCT');
}

/** A union counts as an animation: the backend shows the animation models as `any`. */
export function isAnimationType(type: TypeInfo | null | undefined): boolean {
  return !!findType(type, 'Animation') || !!findType(type, 'Union');
}

/** Selects the control for a parameter of the animation `animName`. */
export function paramControl(param: ParamInfo, animName: string, hasStrips: boolean): ParamControl {
  const type = param.type;
  if (param.kind === VAR_POSITIONAL) return 'animation-list';

  if (type?.name.toLowerCase() === 'list') {
    const inner = type.args?.[0];
    if (inner?.name === 'StripAssignment') return 'strip-assignments';
    if (isColorType(inner)) return 'color-list';
    if (isAnimationType(inner)) return 'animation-list';
  }

  if (isAnimationType(type) && isColorType(type)) return 'color-or-animation';
  if (type?.name === 'Preset' || (animName === 'preset' && param.name === 'name')) return 'preset';
  if (type?.name === 'Literal') return 'literal';
  if (isColorType(type)) return 'color';
  if (isAnimationType(type)) return 'animation';
  if (type?.name === 'bool') return 'bool';
  if (
    type?.name === 'str' &&
    (param.name === 'start' || param.name === 'end' || param.name.includes('time'))
  ) {
    return 'time';
  }
  if ((param.name === 'strip' || param.name === 'strip_index') && type?.name === 'int' && hasStrips) {
    return 'strip';
  }
  if (type?.name === 'int' || type?.name === 'float') return 'number';
  return 'text';
}

/** The options of a `Literal` type. */
export function literalOptions(type: TypeInfo): string[] {
  return (type.args ?? []).map((arg) => arg.name);
}

/** The name of a config entry, or '' if the entry holds no animation. */
export function animationName(config: unknown): string {
  if (!isPlainObject(config)) return '';
  const keys = Object.keys(config);
  return keys.length === 1 ? keys[0] : '';
}

/**
 * True if the value is a color, false if it is an animation. A color has only channel keys
 * (`r`, `g`, `b`, `cw`, `ww`), and the YAML can leave out the channels that are 0.
 */
export function isColorValue(value: unknown): value is Rgbcct {
  if (!isPlainObject(value)) return false;
  const keys = Object.keys(value);
  return keys.length > 0 && keys.every((k) => (CHANNELS as readonly string[]).includes(k));
}

/**
 * A new config entry for the animation, with the defaults of its parameters filled in.
 * An unknown name gives an entry with no parameters.
 */
export function newAnimation(name: string, animations: readonly AnimationInfo[]): AnimationConfig {
  const info = animations.find((a) => a.name === name);
  const params: Record<string, unknown> = {};
  for (const param of info?.params ?? []) {
    if (param.default !== null && param.default !== undefined) {
      params[param.name] = clone(param.default);
    }
  }
  return { [name]: params };
}

/** The first animation, as the entry that an "add" button appends. */
export function defaultChild(animations: readonly AnimationInfo[]): AnimationConfig {
  return { [animations[0]?.name ?? 'static']: {} };
}

/** Limits a channel value to an integer from 0 to 255. Text that is not a number gives 0. */
export function clampChannel(value: unknown): number {
  const n = typeof value === 'number' ? value : parseInt(String(value), 10);
  if (!Number.isFinite(n)) return 0;
  return Math.max(0, Math.min(255, Math.round(n)));
}

/** The CSS color of the RGB part of a color. */
export function cssColor(color: Partial<Rgbcct> | null | undefined): string {
  const c = color ?? BLACK;
  return `rgb(${clampChannel(c.r ?? 0)}, ${clampChannel(c.g ?? 0)}, ${clampChannel(c.b ?? 0)})`;
}

/** The hex value of the RGB part, for `<input type="color">`. */
export function hexColor(color: Partial<Rgbcct> | null | undefined): string {
  const c = color ?? BLACK;
  const hex = (n: unknown) => clampChannel(n ?? 0).toString(16).padStart(2, '0');
  return `#${hex(c.r)}${hex(c.g)}${hex(c.b)}`;
}

/** Parses `#rrggbb` into the RGB channels, or returns null. */
export function parseHex(hex: string): Pick<Rgbcct, 'r' | 'g' | 'b'> | null {
  const m = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  if (!m) return null;
  return { r: parseInt(m[1], 16), g: parseInt(m[2], 16), b: parseInt(m[3], 16) };
}

/** One problem of a draft: the path of the field and the text. */
export interface Problem {
  path: string;
  message: string;
}

/**
 * Finds the problems of an animation draft: no animation selected, an unknown animation,
 * and a number that is not in its limits. The path of a problem is the path that the
 * editor gives the field, for example `blend.animations.0.static.color`.
 */
export function validateAnimation(
  config: unknown,
  animations: readonly AnimationInfo[],
  path = '',
): Problem[] {
  const name = animationName(config);
  if (!name) return [{ path, message: 'Select an animation.' }];
  if (animations.length === 0) return [];
  const info = animations.find((a) => a.name === name);
  if (!info) return [{ path, message: `Unknown animation "${name}".` }];

  const params = (config as AnimationConfig)[name];
  const problems: Problem[] = [];
  for (const param of info.params) {
    const value = isPlainObject(params) ? params[param.name] : undefined;
    const at = join(path, name, param.name);
    problems.push(...checkNumber(param, value, at));
    problems.push(...visitNested(value, animations, at));
  }
  return problems;
}

function checkNumber(param: ParamInfo, value: unknown, path: string): Problem[] {
  const type = param.type?.name;
  if ((type !== 'int' && type !== 'float') || value === undefined || value === null) return [];
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    return [{ path, message: 'Enter a number.' }];
  }
  if (type === 'int' && !Number.isInteger(value)) {
    return [{ path, message: 'Enter a whole number.' }];
  }
  if (param.min !== null && param.min !== undefined && value < param.min) {
    return [{ path, message: `The minimum is ${param.min}.` }];
  }
  if (param.max !== null && param.max !== undefined && value > param.max) {
    return [{ path, message: `The maximum is ${param.max}.` }];
  }
  return [];
}

function visitNested(value: unknown, animations: readonly AnimationInfo[], path: string): Problem[] {
  if (Array.isArray(value)) {
    return value.flatMap((item, i) => visitNested(item, animations, join(path, String(i))));
  }
  if (!isPlainObject(value) || isColorValue(value)) return [];
  const assignment = value['strip_assignment'];
  if (isPlainObject(assignment)) {
    return visitNested(assignment['animation'], animations, join(path, 'strip_assignment', 'animation'));
  }
  return validateAnimation(value, animations, path);
}

function join(...parts: string[]): string {
  return parts.filter((p) => p !== '').join('.');
}

/** A deep copy of JSON data. */
export function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

export function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}
