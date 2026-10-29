import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import type { Observable } from 'rxjs';
import type {
  AnimationConfig,
  AnimationInfo,
  AudioData,
  FloorPoint,
  FpsData,
  GangwayConfig,
  LedColors,
  Preset,
} from './models';

/** The endpoints of the backend API. All paths go through nginx below `/api/`. */
@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);

  config(): Observable<GangwayConfig> {
    return this.http.get<GangwayConfig>('/api/config/');
  }

  /** Saves the config. The backend takes only the animation from it. */
  saveConfig(config: GangwayConfig): Observable<{ message: string }> {
    return this.http.put<{ message: string }>('/api/config/', config);
  }

  animations(): Observable<AnimationInfo[]> {
    return this.http.get<AnimationInfo[]>('/api/animations/');
  }

  presets(): Observable<string[]> {
    return this.http.get<string[]>('/api/presets/');
  }

  preset(name: string): Observable<Preset> {
    return this.http.get<Preset>(`/api/presets/${encodeURIComponent(name)}`);
  }

  /**
   * Saves a preset. With no animation the backend takes the animation of the saved
   * config.
   */
  savePreset(name: string, animation?: AnimationConfig): Observable<{ message: string }> {
    return this.http.post<{ message: string }>(
      `/api/presets/${encodeURIComponent(name)}`,
      animation ?? null,
    );
  }

  loadPreset(name: string): Observable<{ message: string }> {
    return this.http.post<{ message: string }>(
      `/api/presets/${encodeURIComponent(name)}/load`,
      null,
    );
  }

  renamePreset(name: string, newName: string): Observable<{ message: string }> {
    return this.http.post<{ message: string }>(
      `/api/presets/${encodeURIComponent(name)}/rename`,
      null,
      { params: { new_name: newName } },
    );
  }

  deletePreset(name: string): Observable<{ message: string }> {
    return this.http.delete<{ message: string }>(`/api/presets/${encodeURIComponent(name)}`);
  }

  leds(): Observable<LedColors> {
    return this.http.get<LedColors>('/api/data/leds');
  }

  objects(): Observable<FloorPoint[]> {
    return this.http.get<FloorPoint[]>('/api/data/objects');
  }

  fps(): Observable<FpsData> {
    return this.http.get<FpsData>('/api/data/fps');
  }

  audio(): Observable<AudioData> {
    return this.http.get<AudioData>('/api/data/audio');
  }

  homography(): Observable<{ matrix: number[][] }> {
    return this.http.get<{ matrix: number[][] }>('/api/visualization/homography');
  }

  /** One camera frame: `raw` is the camera view, `mapped` the view on the floor plan. */
  liveImage(mode: 'raw' | 'mapped'): Observable<Blob> {
    const path = mode === 'mapped' ? 'live_mapped' : 'live';
    return this.http.get(`/api/visualization/${path}`, { responseType: 'blob' });
  }
}

/** The text for an error of the API: the `detail` of the backend, or the HTTP status. */
export function errorText(error: unknown): string {
  if (error instanceof HttpErrorResponse) {
    const detail: unknown = (error.error as { detail?: unknown } | null)?.detail;
    if (typeof detail === 'string') return detail;
    if (error.status === 0) return 'The server does not answer.';
    return error.statusText || `HTTP ${error.status}`;
  }
  return error instanceof Error ? error.message : String(error);
}
