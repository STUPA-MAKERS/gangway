import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  computed,
  effect,
  inject,
  signal,
  untracked,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { firstValueFrom } from 'rxjs';
import {
  ButtonComponent,
  IconComponent,
  NoteComponent,
  SegmentedComponent,
  type SegmentedOption,
} from '@stupa-makers/ui-kit';
import { ApiService, errorText } from '../../core/api/api.service';
import type {
  CountSeries,
  CountSpan,
  CountSummary,
  CountTotal,
  SensorHealth,
} from '../../core/api/models';
import { CountChartComponent } from '../../features/count-chart/count-chart.component';
import { OccupancyChartComponent } from '../../features/count-chart/occupancy-chart.component';

/** The time between two reads of the counts. The sensor sums them by hour. */
const COUNTS_MS = 60_000;
/** The time between two reads of the health of the sensor. */
const HEALTH_MS = 30_000;

const SPANS: SegmentedOption[] = [
  { value: 'day', label: '24 hours' },
  { value: 'week', label: '7 days' },
  { value: 'month', label: '30 days' },
];

interface Kpi {
  label: string;
  total: CountTotal;
}

interface Fact {
  label: string;
  value: string;
  warn?: boolean;
}

/**
 * The statistics of the people counter (Xovis sensor): totals, the persons over time,
 * the estimate of the persons in the room, the heat map and the health of the sensor.
 *
 * The sensor counts crossings of the entrance line only. The estimate in the room adds
 * the persons in and takes away the persons out, from 0 each morning (see
 * `gangway/xovis/sensor_api.py`). The page calls it an estimate.
 *
 * The backend reads the sensor (`/api/stats/...`) and caches the answers, because the
 * sensor is slow for the heat map. The page reads the counts each minute and the health
 * each 30 s. The heat map loads once; the button loads it again.
 */
@Component({
  selector: 'app-stats-page',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    FormsModule,
    ButtonComponent,
    CountChartComponent,
    IconComponent,
    NoteComponent,
    OccupancyChartComponent,
    SegmentedComponent,
  ],
  templateUrl: './stats.page.html',
  styleUrl: './stats.page.scss',
})
export class StatsPage {
  private readonly api = inject(ApiService);

  protected readonly spans = SPANS;
  protected readonly span = signal<CountSpan>('day');

  protected readonly summary = signal<CountSummary | null>(null);
  protected readonly series = signal<CountSeries | null>(null);
  protected readonly health = signal<SensorHealth | null>(null);
  protected readonly heatmapUrl = signal<string | null>(null);
  protected readonly heatmapLoading = signal(false);
  protected readonly error = signal<string | null>(null);

  protected readonly kpis = computed<Kpi[]>(() => {
    const s = this.summary();
    if (!s) return [];
    return [
      { label: 'Today', total: s.today },
      { label: 'Yesterday', total: s.yesterday },
      { label: 'This week', total: s.week },
      { label: 'Last 30 days', total: s.last_30_days },
      { label: 'All time', total: s.all_time },
    ];
  });

  protected readonly uptimeText = computed(() => duration(this.health()?.uptime ?? 0));

  protected readonly facts = computed<Fact[]>(() => {
    const h = this.health();
    if (!h) return [];
    return [
      { label: 'Mode', value: h.mode || '–', warn: h.mode !== 'tracking' },
      {
        label: 'Light',
        value: h.illumination_ok ? 'Enough to count' : 'Too dark to count',
        warn: !h.illumination_ok,
      },
      { label: 'Running for', value: duration(h.uptime) },
      { label: 'Temperature', value: temperatures(h) },
      {
        label: 'Last event push',
        value: h.push_last_successful ? relativeTime(new Date(h.push_last_successful)) : '–',
      },
      {
        label: 'Event pushes',
        value: `${h.push_successful.toLocaleString()} sent, ${h.push_failed} failed`,
      },
      { label: 'Time sync', value: h.ntp_active ? 'NTP' : 'Off', warn: !h.ntp_active },
      { label: 'Device', value: `${h.device} · ${h.software}` },
    ];
  });

  private active = true;

  constructor() {
    const destroy = inject(DestroyRef);
    destroy.onDestroy(() => {
      this.active = false;
      const url = this.heatmapUrl();
      if (url) URL.revokeObjectURL(url);
    });
    effect(() => {
      const span = this.span();
      untracked(() => void this.readCounts(span));
    });
    void this.every(COUNTS_MS, () => this.readSummary());
    void this.every(COUNTS_MS, () => this.readCounts(this.span()), COUNTS_MS);
    void this.every(HEALTH_MS, () => this.readHealth());
    void this.loadHeatmap();
  }

  protected setSpan(value: string | null): void {
    if (value === 'day' || value === 'week' || value === 'month') this.span.set(value);
  }

  protected async loadHeatmap(): Promise<void> {
    this.heatmapLoading.set(true);
    try {
      const blob = await firstValueFrom(this.api.heatmap());
      const old = this.heatmapUrl();
      this.heatmapUrl.set(URL.createObjectURL(blob));
      if (old) URL.revokeObjectURL(old);
    } catch (error) {
      this.error.set(errorText(error));
    } finally {
      this.heatmapLoading.set(false);
    }
  }

  private async readSummary(): Promise<void> {
    await this.read(async () => this.summary.set(await firstValueFrom(this.api.countSummary())));
  }

  private async readCounts(span: CountSpan): Promise<void> {
    await this.read(async () => {
      const series = await firstValueFrom(this.api.counts(span));
      if (this.span() === span) this.series.set(series);
    });
  }

  private async readHealth(): Promise<void> {
    await this.read(async () => this.health.set(await firstValueFrom(this.api.sensorHealth())));
  }

  private async read(action: () => Promise<void>): Promise<void> {
    try {
      await action();
      this.error.set(null);
    } catch (error) {
      this.error.set(errorText(error));
    }
  }

  /** Runs an action now (or after `delay`) and then every `ms` while the page is open. */
  private async every(ms: number, action: () => Promise<void>, delay = 0): Promise<void> {
    if (delay) await sleep(delay);
    while (this.active) {
      await action();
      await sleep(ms);
    }
  }
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/** A duration in seconds as days and hours, or hours and minutes. */
export function duration(seconds: number): string {
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  if (days > 0) return `${days} d ${hours % 24} h`;
  if (hours > 0) return `${hours} h ${minutes % 60} min`;
  return `${minutes} min`;
}

function relativeTime(date: Date): string {
  const seconds = Math.max(0, Math.round((Date.now() - date.getTime()) / 1000));
  if (seconds < 60) return `${seconds} s ago`;
  return `${duration(seconds)} ago`;
}

function temperatures(h: SensorHealth): string {
  const parts = [
    h.temperature_die !== null ? `chip ${h.temperature_die} °C` : null,
    h.temperature_housing !== null ? `housing ${h.temperature_housing} °C` : null,
  ].filter((p) => p !== null);
  return parts.length ? parts.join(', ') : '–';
}
