/**
 * The data types of the backend API (gangway/api/*.py).
 */

/** One RGBCCT color: red, green, blue, cold white and warm white, each 0..255. */
export interface Rgbcct {
  r: number;
  g: number;
  b: number;
  cw: number;
  ww: number;
}

/**
 * One animation in the config: an object with exactly one key, the animation name. The
 * value holds the parameters, for example `{ "static": { "color": {...} } }`.
 */
export type AnimationConfig = Record<string, AnimationParams>;

/** The parameters of one animation, by parameter name. */
export type AnimationParams = Record<string, unknown>;

/** The description of a parameter type (`TypeInfo` in gangway/api/animations.py). */
export interface TypeInfo {
  name: string;
  args?: TypeInfo[];
  module?: string;
}

/** The description of one animation parameter (`ParamInfo`). */
export interface ParamInfo {
  name: string;
  type: TypeInfo;
  default: unknown;
  kind: number;
  min: number | null;
  max: number | null;
}

/** The description of one animation (`AnimationInfo`). */
export interface AnimationInfo {
  name: string;
  title: string;
  description: string | null;
  params: ParamInfo[];
}

/** One LED strip segment on the floor. */
export interface Strip {
  index: number;
  len: number;
  start: number[];
  end: number[];
}

/** The config file content (`ConfigModel`). */
export interface GangwayConfig {
  projection: {
    src_points: number[][];
    dst_points: number[][];
    floor: number[];
    cutout?: number[][];
  };
  leds: { target_weight: number; offset_x: number; offset_y: number };
  strips: Strip[];
  animation: AnimationConfig;
  audio?: Record<string, unknown> | null;
}

/** A preset with its animation (`PresetModel`). */
export interface Preset {
  name: string;
  animation: AnimationConfig;
}

/** The render and sensor rates (`FpsData`). */
export interface FpsData {
  fps: number;
  tpf_min: number;
  tpf_max: number;
  tpf_avg: number;
  ups: number;
}

/** The sound analysis (`AudioData`). */
export interface AudioData {
  capturing: boolean;
  level: number;
  bass: number;
  mid: number;
  treble: number;
  spectrum: number[];
  beat_count: number;
  since_beat: number | null;
  tempo: number;
}

/** A floor position of a person. */
export interface FloorPoint {
  x: number;
  y: number;
}

/** The colors of all LEDs, by LED index. */
export type LedColors = Record<string, Rgbcct>;

/** The persons in one time bucket of the sensor (`Bucket`). */
export interface CountBucket {
  /** The start of the bucket, ISO 8601 with offset. */
  start: string;
  entered: number;
  left: number;
  /** The estimate of the persons in the room: at the end of an hour, or the peak of a day. */
  occupancy: number;
}

/** A time series of the persons (`GET /api/stats/counts`). */
export interface CountSeries {
  granularity: 'hour' | 'day';
  buckets: CountBucket[];
  entered: number;
  left: number;
}

/** The persons in a time range. */
export interface CountTotal {
  entered: number;
  left: number;
}

/** The totals for the overview (`GET /api/stats/summary`). */
export interface CountSummary {
  today: CountTotal;
  yesterday: CountTotal;
  week: CountTotal;
  last_30_days: CountTotal;
  /** All counts that the sensor keeps (about 4 months). */
  all_time: CountTotal;
  /** The estimate of the persons in the room now. */
  in_room: number;
}

/** The health of the sensor (`GET /api/stats/health`). */
export interface SensorHealth {
  name: string;
  software: string;
  device: string;
  /** Seconds since the last start of the sensor. */
  uptime: number;
  temperature_die: number | null;
  temperature_housing: number | null;
  illumination_ok: boolean;
  mode: string;
  push_last_successful: string | null;
  push_successful: number;
  push_failed: number;
  ntp_active: boolean;
}

/** The time range of the count chart. */
export type CountSpan = 'day' | 'week' | 'month';
