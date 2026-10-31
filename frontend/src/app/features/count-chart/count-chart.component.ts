import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  computed,
  input,
  signal,
  viewChild,
} from '@angular/core';
import { observeElementSize } from '@stupa-makers/ui-kit';
import type { CountBucket, CountSeries } from '../../core/api/models';

/** The height of one half of the chart (in or out) in SVG units. */
const HALF = 100;
/** The share of a bucket width that its bars take. */
const BAR = 0.72;

interface Bar {
  x: number;
  entered: number;
  left: number;
  title: string;
}

export interface Tick {
  /** The position from the start edge in percent. */
  at: number;
  label: string;
}

/**
 * The persons over time as bars: the persons that went in above the axis, the persons
 * that went out below it. Each bar has a tooltip with its time and both values.
 *
 * The bars stretch with the width (`preserveAspectRatio="none"`). The labels are HTML
 * on top of the SVG, so they keep their size.
 */
@Component({
  selector: 'app-count-chart',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="cc">
      <div class="cc__scale" aria-hidden="true">
        <span>{{ max() }}</span>
        <span>0</span>
        <span>{{ max() }}</span>
      </div>
      <div #plot class="cc__plot">
        <svg
          class="cc__svg"
          [attr.viewBox]="'0 0 ' + width() + ' ' + 2 * half"
          preserveAspectRatio="none"
          role="img"
          [attr.aria-label]="label()"
        >
          <line class="cc__axis" x1="0" [attr.x2]="width()" [attr.y1]="half" [attr.y2]="half" />
          @for (bar of bars(); track bar.x) {
            <g class="cc__bucket">
              <title>{{ bar.title }}</title>
              <rect class="cc__hit" [attr.x]="bar.x" y="0" width="1" [attr.height]="2 * half" />
              <rect
                class="cc__in"
                [attr.x]="bar.x + (1 - barShare) / 2"
                [attr.y]="half - scaled(bar.entered)"
                [attr.width]="barShare"
                [attr.height]="scaled(bar.entered)"
              />
              <rect
                class="cc__out"
                [attr.x]="bar.x + (1 - barShare) / 2"
                [attr.y]="half"
                [attr.width]="barShare"
                [attr.height]="scaled(bar.left)"
              />
            </g>
          }
        </svg>
        <div class="cc__ticks" aria-hidden="true">
          @for (tick of ticks(); track tick.at) {
            <span class="cc__tick" [style.left.%]="tick.at">{{ tick.label }}</span>
          }
        </div>
      </div>
    </div>
  `,
  styles: `
    :host {
      display: block;
      min-width: 0;
    }
    .cc {
      display: grid;
      grid-template-columns: auto minmax(0, 1fr);
      gap: var(--space-2);
    }
    .cc__scale {
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      height: 220px;
      color: var(--color-text-muted);
      font-size: var(--fs-small);
      font-variant-numeric: tabular-nums;
      line-height: 1;
      text-align: end;
    }
    .cc__plot {
      min-width: 0;
    }
    .cc__svg {
      display: block;
      width: 100%;
      height: 220px;
    }
    .cc__axis {
      stroke: var(--color-border-strong);
      stroke-width: 1;
      vector-effect: non-scaling-stroke;
    }
    .cc__hit {
      fill: transparent;
    }
    .cc__bucket:hover .cc__hit {
      fill: var(--color-surface-3);
    }
    .cc__in {
      fill: var(--color-accent);
    }
    .cc__out {
      fill: var(--color-info);
    }
    .cc__ticks {
      position: relative;
      height: 1.5rem;
      margin-top: var(--space-1);
    }
    .cc__tick {
      position: absolute;
      top: 0;
      translate: -50% 0;
      color: var(--color-text-muted);
      font-size: var(--fs-small);
      font-variant-numeric: tabular-nums;
      white-space: nowrap;
    }
  `,
})
export class CountChartComponent {
  readonly series = input.required<CountSeries>();

  protected readonly half = HALF;
  protected readonly barShare = BAR;

  protected readonly width = computed(() => Math.max(1, this.series().buckets.length));

  /** The top of the scale: the largest bucket, rounded up to a readable number. */
  protected readonly max = computed(() =>
    niceCeil(Math.max(1, ...this.series().buckets.flatMap((b) => [b.entered, b.left]))),
  );

  protected readonly bars = computed<Bar[]>(() => {
    const { buckets, granularity } = this.series();
    return buckets.map((bucket, i) => ({
      x: i,
      entered: bucket.entered,
      left: bucket.left,
      title: `${bucketLabel(bucket, granularity)}: ${bucket.entered} in, ${bucket.left} out`,
    }));
  });

  private readonly plot = viewChild.required<ElementRef<HTMLElement>>('plot');
  private readonly plotWidth = signal(0);

  protected readonly ticks = computed(() => chartTicks(this.series(), this.plotWidth()));

  constructor() {
    observeElementSize(
      () => this.plot().nativeElement,
      (size) => this.plotWidth.set(size.width),
    );
  }

  protected readonly label = computed(() => {
    const { entered, left } = this.series();
    return `Persons over time: ${entered} in, ${left} out.`;
  });

  protected scaled(value: number): number {
    return (value / this.max()) * HALF;
  }
}

/** Rounds up to 1, 2 or 5 times a power of ten. */
export function niceCeil(value: number): number {
  const power = 10 ** Math.floor(Math.log10(value));
  const step = [1, 2, 5, 10].find((f) => f * power >= value) ?? 10;
  return step * power;
}

/** The smallest distance between two labels below a chart, in px. */
const TICK_GAP = 56;

/**
 * The labels below a chart of the series: hours, weekdays or dates.
 *
 * @param width The width of the plot in px. A narrow plot (a phone) gets fewer labels,
 *   so they do not run into each other. 0 means "not measured": all labels.
 */
export function chartTicks(series: CountSeries, width = 0): Tick[] {
  const { buckets, granularity } = series;
  const n = buckets.length;
  const every = tickStep(n, granularity);
  const ticks = buckets
    .map((bucket, i) => ({ bucket, i }))
    .filter(({ bucket, i }) => isTick(bucket, i, every, granularity, n))
    .map(({ bucket, i }) => ({
      at: ((i + 0.5) / n) * 100,
      label: tickLabel(bucket, granularity, n),
    }));
  const room = width > 0 ? Math.max(2, Math.floor(width / TICK_GAP)) : ticks.length;
  const keep = Math.ceil(ticks.length / room);
  // Thin from the end, so the newest bucket keeps its label.
  return ticks.filter((_tick, i) => (ticks.length - 1 - i) % keep === 0);
}

function tickStep(n: number, granularity: CountSeries['granularity']): number {
  if (granularity === 'day') return n > 14 ? 5 : 1;
  return n > 48 ? 24 : 3;
}

function isTick(
  bucket: CountBucket,
  i: number,
  every: number,
  granularity: CountSeries['granularity'],
  n: number,
): boolean {
  if (granularity === 'day') return (n - 1 - i) % every === 0;
  const hour = new Date(bucket.start).getHours();
  return every === 24 ? hour === 0 : hour % every === 0;
}

const WEEKDAY = new Intl.DateTimeFormat(undefined, { weekday: 'short' });
const DAY = new Intl.DateTimeFormat(undefined, { day: '2-digit', month: '2-digit' });
const HOUR = new Intl.DateTimeFormat(undefined, {
  hour: '2-digit',
  minute: '2-digit',
  hourCycle: 'h23',
});
const FULL = new Intl.DateTimeFormat(undefined, {
  weekday: 'short',
  day: '2-digit',
  month: '2-digit',
});

function tickLabel(
  bucket: CountBucket,
  granularity: CountSeries['granularity'],
  n: number,
): string {
  const date = new Date(bucket.start);
  if (granularity === 'day') return DAY.format(date);
  return n > 48 ? WEEKDAY.format(date) : HOUR.format(date);
}

/** The time of a bucket for a tooltip. */
export function bucketLabel(bucket: CountBucket, granularity: CountSeries['granularity']): string {
  const date = new Date(bucket.start);
  return granularity === 'day' ? FULL.format(date) : `${FULL.format(date)} ${HOUR.format(date)}`;
}
