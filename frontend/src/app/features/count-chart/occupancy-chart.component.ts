import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';
import type { CountSeries } from '../../core/api/models';
import { bucketLabel, chartTicks, niceCeil } from './count-chart.component';

/** The height of the chart in SVG units. */
const HEIGHT = 100;

/**
 * The estimate of the persons in the room as a step area: one step for each bucket. An
 * hour shows the estimate at its end, a day the peak of the day. Each step has a tooltip.
 *
 * The area stretches with the width (`preserveAspectRatio="none"`). The labels are HTML,
 * as in `CountChartComponent`.
 */
@Component({
  selector: 'app-occupancy-chart',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="oc">
      <div class="oc__scale" aria-hidden="true">
        <span>{{ max() }}</span>
        <span>0</span>
      </div>
      <div class="oc__plot">
        <svg
          class="oc__svg"
          [attr.viewBox]="'0 0 ' + width() + ' ' + height"
          preserveAspectRatio="none"
          role="img"
          [attr.aria-label]="label()"
        >
          <path class="oc__area" [attr.d]="area()" />
          <path class="oc__line" [attr.d]="outline()" />
          @for (step of steps(); track step.x) {
            <rect class="oc__hit" [attr.x]="step.x" y="0" width="1" [attr.height]="height">
              <title>{{ step.title }}</title>
            </rect>
          }
        </svg>
        <div class="oc__ticks" aria-hidden="true">
          @for (tick of ticks(); track tick.at) {
            <span class="oc__tick" [style.left.%]="tick.at">{{ tick.label }}</span>
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
    .oc {
      display: grid;
      grid-template-columns: auto minmax(0, 1fr);
      gap: var(--space-2);
    }
    .oc__scale {
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      height: 140px;
      color: var(--color-text-muted);
      font-size: var(--fs-small);
      font-variant-numeric: tabular-nums;
      line-height: 1;
      text-align: end;
    }
    .oc__plot {
      min-width: 0;
    }
    .oc__svg {
      display: block;
      width: 100%;
      height: 140px;
      border-bottom: var(--border-width) solid var(--color-border-strong);
    }
    .oc__area {
      fill: var(--color-accent);
      opacity: 0.25;
    }
    .oc__line {
      fill: none;
      stroke: var(--color-accent);
      stroke-width: 2;
      vector-effect: non-scaling-stroke;
    }
    .oc__hit {
      fill: transparent;
    }
    .oc__hit:hover {
      fill: var(--color-surface-3);
      opacity: 0.6;
    }
    .oc__ticks {
      position: relative;
      height: 1.5rem;
      margin-top: var(--space-1);
    }
    .oc__tick {
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
export class OccupancyChartComponent {
  readonly series = input.required<CountSeries>();

  protected readonly height = HEIGHT;

  protected readonly width = computed(() => Math.max(1, this.series().buckets.length));

  protected readonly max = computed(() =>
    niceCeil(Math.max(1, ...this.series().buckets.map((b) => b.occupancy))),
  );

  /** The top edge of the steps, from the start to the end of the chart. */
  private readonly points = computed(() => {
    const max = this.max();
    return this.series().buckets.flatMap((b, i) => {
      const y = HEIGHT - (b.occupancy / max) * HEIGHT;
      return [
        [i, y],
        [i + 1, y],
      ];
    });
  });

  protected readonly outline = computed(() =>
    this.points()
      .map(([x, y], i) => `${i ? 'L' : 'M'}${x},${y}`)
      .join(''),
  );

  protected readonly area = computed(() => {
    const line = this.outline();
    return line ? `${line}L${this.width()},${HEIGHT}L0,${HEIGHT}Z` : '';
  });

  protected readonly steps = computed(() => {
    const { buckets, granularity } = this.series();
    const what = granularity === 'day' ? 'at most' : 'about';
    return buckets.map((bucket, i) => ({
      x: i,
      title: `${bucketLabel(bucket, granularity)}: ${what} ${bucket.occupancy} in the room`,
    }));
  });

  protected readonly ticks = computed(() => chartTicks(this.series()));

  protected readonly label = computed(() => {
    const peak = Math.max(0, ...this.series().buckets.map((b) => b.occupancy));
    return `Estimated persons in the room over time, at most ${peak}.`;
  });
}
