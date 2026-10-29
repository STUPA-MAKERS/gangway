import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  ElementRef,
  NgZone,
  afterNextRender,
  computed,
  effect,
  inject,
  input,
  signal,
  untracked,
  viewChild,
} from '@angular/core';
import { firstValueFrom, forkJoin } from 'rxjs';
import {
  ButtonComponent,
  IconComponent,
  SegmentedComponent,
  type SegmentedOption,
} from '@stupa-makers/ui-kit';
import { ApiService } from '../../core/api/api.service';
import type { FloorPoint, FpsData, GangwayConfig, LedColors } from '../../core/api/models';
import { AudioMeterComponent } from '../audio-meter/audio-meter.component';
import { type Matrix3, containFit, invert3, project, segmentDistance2 } from './geometry';

export type ViewMode = 'mapped' | 'raw';

const VIEW_OPTIONS: SegmentedOption[] = [
  { value: 'mapped', label: 'Mapped' },
  { value: 'raw', label: 'Raw' },
];

const VIEW_KEY = 'gangway.view';

/** The stored view, or `raw`, the view of the camera. */
function readViewMode(): ViewMode {
  try {
    return localStorage.getItem(VIEW_KEY) === 'mapped' ? 'mapped' : 'raw';
  } catch {
    return 'raw';
  }
}

/** The poll interval of the LED colors, the persons and the rates. */
const DATA_INTERVAL_MS = 50;
/** The poll interval of the camera image while the live image is on. */
const IMAGE_INTERVAL_MS = 200;
/** The wait after a failed camera image. */
const IMAGE_RETRY_MS = 5000;
/** The squared floor distance in which the pointer selects a strip. */
const HOVER_DISTANCE2 = 100;

/**
 * The live view of the installation: the strips in their current colors, the detected
 * persons and the camera image.
 *
 * - `mapped` draws on the floor plan. The camera image, mapped onto the floor, is faint
 *   in the background.
 * - `raw` draws on the camera image. The inverse homography moves the floor positions into
 *   the image.
 *
 * The data and the image arrive through polls, and the canvas draws in an animation frame.
 * All three run outside the Angular zone, so they do not start a change detection.
 */
@Component({
  selector: 'app-visualization',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [ButtonComponent, IconComponent, SegmentedComponent, AudioMeterComponent],
  templateUrl: './visualization.component.html',
  styleUrl: './visualization.component.scss',
})
export class VisualizationComponent {
  private readonly api = inject(ApiService);
  private readonly zone = inject(NgZone);

  readonly config = input.required<GangwayConfig>();
  /** Shows the bar with the view controls. */
  readonly controls = input(true);

  protected readonly viewOptions = VIEW_OPTIONS;
  protected readonly viewMode = signal<ViewMode>(readViewMode());
  protected readonly showImage = signal(false);
  protected readonly showObjects = signal(true);
  protected readonly showAudio = signal(false);
  protected readonly stats = signal<FpsData | null>(null);
  protected readonly imageSrc = signal('');
  protected readonly imageReady = signal(false);
  protected readonly imageFailed = signal(false);
  protected readonly imageDims = signal({ width: 0, height: 0 });
  protected readonly scale = signal(1);
  protected readonly hovered = signal<number | null>(null);
  private readonly homography = signal<Matrix3 | null>(null);
  private readonly inverse = computed(() => {
    const h = this.homography();
    return h ? invert3(h) : null;
  });

  protected readonly floorWidth = computed(() => this.config().projection.floor[2] || 800);
  protected readonly floorHeight = computed(() => this.config().projection.floor[3] || 600);
  protected readonly strips = computed(() => this.config().strips);

  /** The drawing is visible: the mapped view, or the raw view with an image. */
  protected readonly visible = computed(() => this.viewMode() === 'mapped' || this.imageReady());

  protected readonly canvasWidth = computed(() =>
    this.viewMode() === 'raw' ? this.imageDims().width || 1280 : this.floorWidth(),
  );
  protected readonly canvasHeight = computed(() =>
    this.viewMode() === 'raw' ? this.imageDims().height || 720 : this.floorHeight(),
  );

  private readonly container = viewChild.required<ElementRef<HTMLElement>>('container');
  private readonly canvas = viewChild.required<ElementRef<HTMLCanvasElement>>('canvas');

  private leds: LedColors = {};
  private objects: FloorPoint[] = [];
  private pointer = { x: -1000, y: -1000 };
  private active = true;
  private imageTimer: ReturnType<typeof setTimeout> | null = null;
  private imageBusy = false;
  private imageOnce = false;
  private lastObjectUrl: string | null = null;
  private lastHover: number | null = null;

  constructor() {
    const destroyRef = inject(DestroyRef);
    destroyRef.onDestroy(() => {
      this.active = false;
      if (this.imageTimer) clearTimeout(this.imageTimer);
      if (this.lastObjectUrl) URL.revokeObjectURL(this.lastObjectUrl);
    });

    afterNextRender(() => {
      this.zone.runOutsideAngular(() => {
        void this.pollData();
        this.watchSize(destroyRef);
        this.startRender(destroyRef);
      });
    });

    firstValueFrom(this.api.homography())
      .then((data) => this.homography.set(data.matrix))
      .catch(() => undefined);

    // A change of the view or of the live switch loads one new frame at once.
    effect(() => {
      this.viewMode();
      this.showImage();
      untracked(() => {
        this.imageOnce = false;
        this.imageFailed.set(false);
        if (this.imageTimer) clearTimeout(this.imageTimer);
        this.zone.runOutsideAngular(() => void this.loadImage());
      });
    });
  }

  protected setView(mode: string | null): void {
    if (mode !== 'mapped' && mode !== 'raw') return;
    this.viewMode.set(mode);
    try {
      localStorage.setItem(VIEW_KEY, mode);
    } catch {
      /* The view then lasts for this page only. */
    }
  }

  protected onPointerMove(event: PointerEvent): void {
    const rect = this.container().nativeElement.getBoundingClientRect();
    this.pointer = { x: event.clientX - rect.left, y: event.clientY - rect.top };
  }

  protected onPointerLeave(): void {
    this.pointer = { x: -1000, y: -1000 };
  }

  private async pollData(): Promise<void> {
    while (this.active) {
      try {
        const data = await firstValueFrom(
          forkJoin({ leds: this.api.leds(), objects: this.api.objects(), fps: this.api.fps() }),
        );
        this.leds = data.leds;
        this.objects = data.objects;
        const prev = this.stats();
        if (!prev || prev.fps !== data.fps.fps || prev.ups !== data.fps.ups) {
          this.stats.set(data.fps);
        }
      } catch {
        /* The next poll tries again. */
      }
      await sleep(DATA_INTERVAL_MS);
    }
  }

  private async loadImage(): Promise<void> {
    if (!this.active) return;
    if (this.imageBusy) {
      this.imageTimer = setTimeout(() => void this.loadImage(), IMAGE_INTERVAL_MS);
      return;
    }
    if (!this.showImage() && this.imageOnce) return;
    this.imageBusy = true;
    let delay = IMAGE_INTERVAL_MS;
    try {
      const blob = await firstValueFrom(this.api.liveImage(this.viewMode()));
      await this.showBlob(blob);
      this.imageFailed.set(false);
    } catch {
      // A missing camera fails each time, so the next try waits longer.
      this.imageFailed.set(true);
      delay = IMAGE_RETRY_MS;
    } finally {
      this.imageBusy = false;
    }
    if (this.active) {
      this.imageTimer = setTimeout(() => void this.loadImage(), delay);
    }
  }

  private showBlob(blob: Blob): Promise<void> {
    const url = URL.createObjectURL(blob);
    return new Promise((resolve) => {
      const img = new Image();
      img.onload = () => {
        if (this.active) {
          this.imageDims.set({ width: img.naturalWidth, height: img.naturalHeight });
          if (this.lastObjectUrl) URL.revokeObjectURL(this.lastObjectUrl);
          this.lastObjectUrl = url;
          this.imageSrc.set(url);
          this.imageReady.set(true);
          this.imageOnce = true;
        } else {
          URL.revokeObjectURL(url);
        }
        resolve();
      };
      img.onerror = () => {
        URL.revokeObjectURL(url);
        resolve();
      };
      img.src = url;
    });
  }

  private watchSize(destroyRef: DestroyRef): void {
    const el = this.container().nativeElement;
    const update = () => {
      const margin = 40;
      const sx = (el.clientWidth - margin) / this.floorWidth();
      const sy = (el.clientHeight - margin) / this.floorHeight();
      const s = Math.max(0.01, Math.min(sx, sy));
      if (s !== this.scale()) this.scale.set(s);
    };
    const observer = new ResizeObserver(update);
    observer.observe(el);
    update();
    destroyRef.onDestroy(() => observer.disconnect());
  }

  private startRender(destroyRef: DestroyRef): void {
    let frame = 0;
    const loop = () => {
      this.draw();
      frame = requestAnimationFrame(loop);
    };
    frame = requestAnimationFrame(loop);
    destroyRef.onDestroy(() => cancelAnimationFrame(frame));
  }

  /** Draws one frame. Public for the tests. */
  draw(): void {
    const ctx = this.canvas().nativeElement.getContext('2d');
    if (!ctx) return;
    ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);

    const raw = this.viewMode() === 'raw';
    if (raw && !this.imageReady()) return;

    const floorW = this.floorWidth();
    const floorH = this.floorHeight();
    const h = this.homography();
    const inv = this.inverse();
    const [mx, my] = this.pointerOnFloor(raw, floorW, floorH, h);

    const toCanvas = (fx: number, fy: number): [number, number] =>
      raw && inv ? project(fx, floorH - fy, inv) : [fx, fy];

    let best = HOVER_DISTANCE2;
    let hover: number | null = null;
    const hovered = this.hovered();

    this.strips().forEach((strip, idx) => {
      const [sx, sy] = strip.start;
      const [ex, ey] = strip.end;
      const d2 = segmentDistance2(mx, my, sx, sy, ex, ey);
      if (d2 < best) {
        best = d2;
        hover = idx;
      }

      const [x1, y1] = toCanvas(sx, sy);
      const [x2, y2] = toCanvas(ex, ey);
      const grad = ctx.createLinearGradient(x1, y1, x2, y2);
      for (let i = 0; i < strip.len; i++) {
        const c = this.leds[strip.index + i];
        const stop = i / (strip.len - 1 || 1);
        if (c) {
          const white = c.cw + c.ww;
          grad.addColorStop(
            stop,
            `rgb(${Math.min(255, c.r + white)},${Math.min(255, c.g + white)},${Math.min(255, c.b + white)})`,
          );
        } else {
          grad.addColorStop(stop, '#111');
        }
      }

      let width = 4;
      if (raw && inv) {
        const z =
          inv[2][0] * ((sx + ex) / 2) + inv[2][1] * (floorH - (sy + ey) / 2) + inv[2][2];
        width = Math.max(1, Math.min(10, 2.5 / (z || 1)));
      }

      ctx.lineCap = 'round';
      if (hovered === idx) {
        ctx.shadowBlur = 15;
        ctx.shadowColor = 'white';
        ctx.strokeStyle = 'rgba(255,255,255,0.9)';
        ctx.lineWidth = width + 4;
        line(ctx, x1, y1, x2, y2);
        ctx.shadowBlur = 0;
      }
      ctx.strokeStyle = 'rgba(0,0,0,0.5)';
      ctx.lineWidth = width + 1.5;
      line(ctx, x1, y1, x2, y2);
      ctx.strokeStyle = grad;
      ctx.lineWidth = width;
      line(ctx, x1, y1, x2, y2);
    });

    if (this.showObjects()) {
      ctx.fillStyle = 'rgba(255, 0, 0, 0.7)';
      ctx.strokeStyle = 'white';
      ctx.lineWidth = 1;
      for (const obj of this.objects) {
        const [ox, oy] = toCanvas(obj.x, obj.y);
        ctx.beginPath();
        ctx.arc(ox, oy, 6, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
      }
    }

    // Only a change of the hit under the pointer sets the strip. A strip that the legend
    // selected stays selected while the pointer does not move to another strip.
    if (hover !== this.lastHover) {
      this.lastHover = hover;
      this.hovered.set(hover);
    }
  }

  /** The pointer position in floor coordinates. */
  private pointerOnFloor(
    raw: boolean,
    floorW: number,
    floorH: number,
    h: Matrix3 | null,
  ): [number, number] {
    const { x, y } = this.pointer;
    if (x <= -1000) return [-1000, -1000];
    const el = this.container().nativeElement;
    if (!raw) {
      const s = this.scale();
      return [(x - el.clientWidth / 2) / s + floorW / 2, (y - el.clientHeight / 2) / s + floorH / 2];
    }
    const dims = this.imageDims();
    if (dims.width <= 0 || !h) return [-1000, -1000];
    const fit = containFit(el.clientWidth, el.clientHeight, dims.width, dims.height);
    const imgX = ((x - fit.x) / fit.width) * dims.width;
    const imgY = ((y - fit.y) / fit.height) * dims.height;
    const [fx, fy] = project(imgX, imgY, h);
    return [fx, floorH - fy];
  }
}

function line(ctx: CanvasRenderingContext2D, x1: number, y1: number, x2: number, y2: number): void {
  ctx.beginPath();
  ctx.moveTo(x1, y1);
  ctx.lineTo(x2, y2);
  ctx.stroke();
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
