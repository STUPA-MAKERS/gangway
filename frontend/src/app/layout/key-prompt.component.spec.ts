import { fireEvent, render, screen } from '@testing-library/angular';
import { KeyPromptComponent } from './key-prompt.component';

describe('KeyPromptComponent', () => {
  it('emits the key on submit', async () => {
    const unlock = jest.fn();
    await render(KeyPromptComponent, { on: { unlock } });
    const field = screen.getByLabelText('API key', { selector: 'input' });
    fireEvent.input(field, { target: { value: '  secret ' } });
    fireEvent.click(screen.getByRole('button', { name: 'Unlock' }));
    expect(unlock).toHaveBeenCalledWith('secret');
  });

  it('shows the refusal', async () => {
    await render(KeyPromptComponent, { inputs: { rejected: true } });
    expect(screen.getByRole('alert')).toHaveTextContent('The server does not accept this key.');
  });
});
