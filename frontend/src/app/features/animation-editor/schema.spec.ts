import type { AnimationInfo, ParamInfo, TypeInfo } from '../../core/api/models';
import {
  clampChannel,
  hexColor,
  isColorValue,
  newAnimation,
  paramControl,
  parseHex,
  validateAnimation,
} from './schema';

const any: TypeInfo = { name: 'any' };
const animOrColor: TypeInfo = { name: 'Union', args: [any, any, { name: 'RGBCCT' }] };

function param(name: string, type: TypeInfo, extra: Partial<ParamInfo> = {}): ParamInfo {
  return { name, type, default: null, kind: 1, min: null, max: null, ...extra };
}

const ANIMATIONS: AnimationInfo[] = [
  {
    name: 'blend',
    title: 'Blend (Meta)',
    description: null,
    params: [
      param('animations', { name: 'list', args: [{ name: 'Union', args: [any, any] }] }),
      param('mode', { name: 'Literal', args: [{ name: 'average' }, { name: 'max' }] }, {
        default: 'average',
      }),
    ],
  },
  {
    name: 'static',
    title: 'Static Color',
    description: null,
    params: [
      param('color', { name: 'RGBCCT' }, { default: { r: 255, g: 0, b: 0, cw: 0, ww: 0 } }),
    ],
  },
  {
    name: 'rainbow',
    title: 'Rainbow',
    description: null,
    params: [
      param('speed', { name: 'float' }, { default: 0.1, min: 0 }),
      param('count', { name: 'int' }, { min: 1, max: 10 }),
    ],
  },
  {
    name: 'beat_pulse',
    title: 'Beat Pulse (Audio)',
    description: null,
    params: [param('background', animOrColor)],
  },
];

describe('paramControl', () => {
  it('maps the backend types to controls', () => {
    expect(paramControl(ANIMATIONS[0].params[0], 'blend', false)).toBe('animation-list');
    expect(paramControl(ANIMATIONS[0].params[1], 'blend', false)).toBe('literal');
    expect(paramControl(ANIMATIONS[1].params[0], 'static', false)).toBe('color');
    expect(paramControl(ANIMATIONS[2].params[0], 'rainbow', false)).toBe('number');
    expect(paramControl(ANIMATIONS[3].params[0], 'beat_pulse', false)).toBe('color-or-animation');
    expect(paramControl(param('assignments', { name: 'list', args: [{ name: 'StripAssignment' }] }), 'by_strip', false)).toBe('strip-assignments');
    expect(paramControl(param('colors', { name: 'list', args: [{ name: 'RGBCCT' }] }), 'wave', false)).toBe('color-list');
    expect(paramControl(param('name', { name: 'str' }), 'preset', false)).toBe('preset');
    expect(paramControl(param('start', { name: 'str' }), 'schedule', false)).toBe('time');
    expect(paramControl(param('reverse', { name: 'bool' }), 'level', false)).toBe('bool');
    expect(paramControl(param('label', { name: 'str' }), 'x', false)).toBe('text');
  });

  it('shows a strip select only if the config has strips', () => {
    const strip = param('strip', { name: 'int' });
    expect(paramControl(strip, 'x', true)).toBe('strip');
    expect(paramControl(strip, 'x', false)).toBe('number');
  });
});

describe('newAnimation', () => {
  it('fills in the defaults', () => {
    expect(newAnimation('blend', ANIMATIONS)).toEqual({ blend: { mode: 'average' } });
    expect(newAnimation('rainbow', ANIMATIONS)).toEqual({ rainbow: { speed: 0.1 } });
  });

  it('copies an object default', () => {
    const a = newAnimation('static', ANIMATIONS);
    const b = newAnimation('static', ANIMATIONS);
    expect(a['static']['color']).not.toBe(b['static']['color']);
  });
});

describe('colors', () => {
  it('tells a color from an animation', () => {
    expect(isColorValue({ r: 1, g: 2, b: 3, cw: 0, ww: 0 })).toBe(true);
    expect(isColorValue({ ww: 255 })).toBe(true);
    expect(isColorValue({ rainbow: {} })).toBe(false);
    expect(isColorValue({})).toBe(false);
  });

  it('clamps the channels and converts hex', () => {
    expect(clampChannel(300)).toBe(255);
    expect(clampChannel(-4)).toBe(0);
    expect(clampChannel('abc')).toBe(0);
    expect(hexColor({ r: 255, g: 16, b: 0 })).toBe('#ff1000');
    expect(parseHex('#ff1000')).toEqual({ r: 255, g: 16, b: 0 });
    expect(parseHex('nope')).toBeNull();
  });
});

describe('validateAnimation', () => {
  it('accepts a valid nested draft', () => {
    const draft = {
      blend: { animations: [{ rainbow: { speed: 1, count: 3 } }, { static: {} }], mode: 'max' },
    };
    expect(validateAnimation(draft, ANIMATIONS)).toEqual([]);
  });

  it('asks for an animation', () => {
    expect(validateAnimation({}, ANIMATIONS)).toEqual([{ path: '', message: 'Select an animation.' }]);
  });

  it('finds numbers out of their limits, with the path of the field', () => {
    const draft = { blend: { animations: [{ rainbow: { speed: -1, count: 2.5 } }] } };
    expect(validateAnimation(draft, ANIMATIONS)).toEqual([
      { path: 'blend.animations.0.rainbow.speed', message: 'The minimum is 0.' },
      { path: 'blend.animations.0.rainbow.count', message: 'Enter a whole number.' },
    ]);
  });

  it('checks the animation of a color-or-animation parameter', () => {
    expect(validateAnimation({ beat_pulse: { background: { r: 0 } } }, ANIMATIONS)).toEqual([]);
    expect(validateAnimation({ beat_pulse: { background: { nope: {} } } }, ANIMATIONS)).toEqual([
      { path: 'beat_pulse.background', message: 'Unknown animation "nope".' },
    ]);
  });
});
