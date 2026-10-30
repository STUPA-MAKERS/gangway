import { ChangeDetectionStrategy, Component, signal } from '@angular/core';
import { provideRouter } from '@angular/router';
import { fireEvent, render, screen } from '@testing-library/angular';
import { App } from './app';
import { type LoadState, ConfigStore } from './core/state/config-store.service';

@Component({
  selector: 'app-test-page',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: '<p>The page</p>',
})
class TestPage {}

/** A store without a backend: the test sets the load state. */
class FakeStore {
  readonly state = signal<LoadState>('loading');
  readonly error = signal('');
  readonly dirty = signal(false);
  readonly load = jest.fn(async () => undefined);
}

async function setup(state: LoadState) {
  const store = new FakeStore();
  store.state.set(state);
  const view = await render(App, {
    providers: [
      provideRouter([{ path: '**', component: TestPage }]),
      { provide: ConfigStore, useValue: store },
    ],
  });
  return { store, view };
}

describe('App', () => {
  it('shows the navigation and the theme switch of the shell', async () => {
    await setup('ready');
    for (const label of ['Live', 'Animation', 'Presets', 'Statistics']) {
      expect(screen.getByRole('link', { name: label })).toBeInTheDocument();
    }
    expect(screen.getByRole('button', { name: 'Dark' })).toBeInTheDocument();
  });

  it('shows the page once the first load is done', async () => {
    const { view } = await setup('ready');
    await view.navigate('/live');
    expect(await screen.findByText('The page')).toBeInTheDocument();
  });

  it('shows a spinner and no page during the first load', async () => {
    await setup('loading');
    expect(screen.getByRole('status', { name: 'Loading' })).toBeInTheDocument();
    expect(screen.queryByText('The page')).not.toBeInTheDocument();
  });

  it('asks for the key when the backend refuses it', async () => {
    await setup('locked');
    expect(screen.getByRole('heading', { name: 'API key' })).toBeInTheDocument();
  });

  it('loads again from the offline state', async () => {
    const { store } = await setup('offline');
    expect(screen.getByText('You are offline')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Try again' }));
    expect(store.load).toHaveBeenCalledTimes(2);
  });
});
