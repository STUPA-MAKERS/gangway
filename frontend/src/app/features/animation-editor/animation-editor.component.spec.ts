import { fireEvent, render, screen } from '@testing-library/angular';
import type { AnimationInfo } from '../../core/api/models';
import { AnimationEditorComponent, humanize } from './animation-editor.component';

const ANIMATIONS: AnimationInfo[] = [
  {
    name: 'beat_pulse',
    title: 'Beat Pulse (Audio)',
    description: 'Flashes all LEDs on each beat and fades out.',
    params: [
      {
        name: 'background',
        type: { name: 'Union', args: [{ name: 'any' }, { name: 'RGBCCT' }] },
        default: null,
        kind: 1,
        min: null,
        max: null,
      },
      { name: 'decay', type: { name: 'float' }, default: 0.25, kind: 1, min: 0, max: null },
    ],
  },
  { name: 'off', title: 'Off', description: null, params: [] },
];

async function setup(value: unknown) {
  const changed = jest.fn();
  await render(AnimationEditorComponent, {
    inputs: { value, animations: ANIMATIONS },
    on: { changed },
  });
  return changed;
}

describe('AnimationEditorComponent', () => {
  it('shows the parameters of the animation from the schema', async () => {
    await setup({ beat_pulse: { decay: 0.5 } });
    expect(screen.getByText('Flashes all LEDs on each beat and fades out.')).toBeInTheDocument();
    expect(await screen.findByDisplayValue('0.5')).toBe(screen.getByLabelText('Decay'));
    expect(screen.getByText('Background')).toBeInTheDocument();
  });

  it('emits a number change', async () => {
    const changed = await setup({ beat_pulse: { decay: 0.5 } });
    fireEvent.input(screen.getByLabelText('Decay'), { target: { value: '0.75' } });
    expect(changed).toHaveBeenLastCalledWith({ beat_pulse: { decay: 0.75 } });
  });

  it('removes a cleared number, so the backend default applies', async () => {
    const changed = await setup({ beat_pulse: { decay: 0.5 } });
    fireEvent.input(screen.getByLabelText('Decay'), { target: { value: '' } });
    expect(changed).toHaveBeenLastCalledWith({ beat_pulse: {} });
  });

  it('switches a parameter from a color to an animation', async () => {
    const changed = await setup({ beat_pulse: { background: { r: 0, g: 0, b: 0, cw: 0, ww: 0 } } });
    fireEvent.click(screen.getByRole('radio', { name: 'Animation' }));
    expect(changed).toHaveBeenLastCalledWith({ beat_pulse: { background: { beat_pulse: {} } } });
  });

  it('emits a channel change of a color', async () => {
    const changed = await setup({ beat_pulse: { background: { r: 0, g: 0, b: 0, cw: 0, ww: 0 } } });
    fireEvent.change(screen.getByLabelText('Warm white'), { target: { value: '300' } });
    expect(changed).toHaveBeenLastCalledWith({
      beat_pulse: { background: { r: 0, g: 0, b: 0, cw: 0, ww: 255 } },
    });
  });

  it('shows the problem of a field', async () => {
    await render(AnimationEditorComponent, {
      inputs: {
        value: { beat_pulse: { decay: -1 } },
        animations: ANIMATIONS,
        problems: [{ path: 'beat_pulse.decay', message: 'The minimum is 0.' }],
      },
    });
    expect(screen.getByRole('alert')).toHaveTextContent('The minimum is 0.');
  });
});

describe('humanize', () => {
  it('turns a parameter name into a label', () => {
    expect(humanize('max_radius')).toBe('Max radius');
  });
});
