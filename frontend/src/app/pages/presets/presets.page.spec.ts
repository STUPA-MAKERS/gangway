import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { fireEvent, render, screen, waitFor } from '@testing-library/angular';
import { ConfigStore } from '../../core/state/config-store.service';
import { PresetsPage, nameError } from './presets.page';

async function setup(name?: string) {
  await render(PresetsPage, {
    providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    inputs: name ? { name } : {},
  });
  const store = TestBed.inject(ConfigStore);
  store.presets.set(['Musik', 'Rainbow']);
  store.draft.set({ off: {} });
  const backend = TestBed.inject(HttpTestingController);
  return { store, backend };
}

describe('PresetsPage', () => {
  it('lists the presets', async () => {
    await setup();
    expect(await screen.findByText('Musik')).toBeInTheDocument();
    expect(screen.getByText('Rainbow')).toBeInTheDocument();
  });

  it('opens a preset in the editor', async () => {
    const { backend } = await setup('Musik');
    backend.expectOne('/api/presets/Musik').flush({ name: 'Musik', animation: { off: {} } });
    expect(await screen.findByRole('heading', { name: 'Musik' })).toBeInTheDocument();
  });

  it('loads a preset and reads the config again', async () => {
    const { backend } = await setup('Musik');
    backend.expectOne('/api/presets/Musik').flush({ name: 'Musik', animation: { off: {} } });
    fireEvent.click(await screen.findByRole('button', { name: 'Load Musik' }));
    backend.expectOne({ method: 'POST', url: '/api/presets/Musik/load' }).flush({ message: 'ok' });
    await waitFor(() => backend.expectOne('/api/config/'));
  });

  it('saves the draft as a new preset', async () => {
    const { backend } = await setup();
    fireEvent.click(screen.getByRole('button', { name: 'New preset' }));
    fireEvent.input(await screen.findByLabelText('Name'), { target: { value: 'Neu 1' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save' }));
    const req = backend.expectOne({ method: 'POST', url: '/api/presets/Neu%201' });
    expect(req.request.body).toEqual({ off: {} });
    req.flush({ message: 'ok' });
    await waitFor(() => backend.expectOne('/api/presets/').flush(['Musik', 'Neu 1', 'Rainbow']));
    expect(await screen.findByText('Neu 1')).toBeInTheDocument();
  });
});

describe('nameError', () => {
  it('accepts the characters of the backend', () => {
    expect(nameError('My preset-1_a')).toBe('');
    expect(nameError('')).toBe('');
    expect(nameError('a/b')).not.toBe('');
  });
});
