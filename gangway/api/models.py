"""Pydantic models that validate the animation config.

Each animation has a parameter model and a wrapper model. The wrapper model
has one field. The field name is the animation name, and the field type is
the parameter model. The animations endpoint reads these models to describe
the animations to the frontend.

The models use ``Union`` and ``Optional``, not ``X | Y``. The animations
endpoint reports the name of the typing origin, and ``X | Y`` changes that
name from ``Union`` to ``UnionType``.
"""

from typing import Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class RGBCCTModel(BaseModel):
    """Represents an RGBCCT color."""

    r: int = Field(0, ge=0, le=255)
    g: int = Field(0, ge=0, le=255)
    b: int = Field(0, ge=0, le=255)
    cw: int = Field(0, ge=0, le=255)
    ww: int = Field(0, ge=0, le=255)


class AlternateParams(BaseModel):
    """Parameters for the alternate animation."""

    animations: list["AnimationModel"] = Field(default_factory=list)
    length: float = Field(default=10, ge=0)


class FireParams(BaseModel):
    """Parameters for the fire animation."""

    base_color: RGBCCTModel = Field(default=RGBCCTModel(r=255, g=140, b=0, cw=0, ww=0))
    flicker_speed: float = Field(default=0.1, ge=0)
    flicker_intensity: float = Field(default=0.5, ge=0, le=1)


class RainbowParams(BaseModel):
    """Parameters for the rainbow animation."""

    speed: float = Field(default=0.1, ge=0)
    spread: float = Field(default=3.0, ge=0)


class StaticParams(BaseModel):
    """Parameters for the static animation."""

    color: RGBCCTModel = Field(default=RGBCCTModel(r=255, g=255, b=255, cw=0, ww=0))


class StroboParams(BaseModel):
    """Parameters for the strobo animation."""

    colors: list[RGBCCTModel] = Field(
        default=[
            RGBCCTModel(r=255, g=255, b=255, cw=255, ww=255),
            RGBCCTModel(r=0, g=0, b=0, cw=0, ww=0),
            RGBCCTModel(r=255, g=0, b=0, cw=0, ww=0),
            RGBCCTModel(r=0, g=0, b=0, cw=0, ww=0),
            RGBCCTModel(r=0, g=0, b=255, cw=0, ww=0),
        ]
    )
    frequency: int = Field(default=100, ge=0)


class SwingParams(BaseModel):
    """Parameters for the swing animation."""

    color: RGBCCTModel = Field(default=RGBCCTModel(r=255, g=255, b=255, cw=255, ww=0))
    direction: Literal["x", "y"] = "y"
    wavelength: int = Field(default=50, ge=0)
    speed: float = Field(default=10, ge=0)


class Theater_chaseParams(BaseModel):
    """Parameters for the theater_chase animation."""

    color: RGBCCTModel = Field(default=RGBCCTModel(r=255, g=255, b=255, cw=0, ww=0))
    speed: float = Field(default=1.0, ge=0)
    spacing: int = Field(default=4, ge=0)


class WaveParams(BaseModel):
    """Parameters for the wave animation."""

    colors: list[RGBCCTModel] = Field(default_factory=list)
    n_waves: int = Field(default=3, ge=0)
    speed: float = Field(default=50.0, ge=0)
    wavelength: float = Field(default=200.0, ge=0)


class DotParams(BaseModel):
    """Parameters for the dot animation."""

    primary: Optional[Union["AnimationModel", RGBCCTModel]] = None
    secondary: Optional[Union["AnimationModel", RGBCCTModel]] = None
    radius: float = Field(default=150, ge=0)


class ExponentialParams(BaseModel):
    """Parameters for the exponential animation."""

    primary: Union["AnimationModel", RGBCCTModel] = Field(
        default=RGBCCTModel(r=255, g=0, b=0, cw=0, ww=0)
    )
    secondary: Union["AnimationModel", RGBCCTModel] = Field(
        default=RGBCCTModel(r=0, g=255, b=0, cw=0, ww=0)
    )
    radius: float = Field(default=150, ge=0)


class OffParams(BaseModel):
    """Parameters for the off animation."""


class IdleParams(BaseModel):
    """Parameters for the idle animation."""

    idle_animation: Union["AnimationModel", RGBCCTModel] = Field(
        default=RGBCCTModel(r=255, g=0, b=0, cw=0, ww=0)
    )
    active_animation: Union["AnimationModel", RGBCCTModel] = Field(
        default=RGBCCTModel(r=0, g=255, b=0, cw=0, ww=0)
    )

    model_config = ConfigDict(extra="forbid")


class BlendParams(BaseModel):
    """Parameters for the blend animation."""

    animations: list["AnimationModel"] = Field(default_factory=list)
    mode: Literal["average", "max"] = "average"


class RaveParams(BaseModel):
    """Parameters for the rave animation."""


class ScheduleParams(BaseModel):
    """Parameters for the schedule animation."""

    start: str = Field(default="18:00", pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    end: str = Field(default="06:00", pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    primary: Union["AnimationModel", RGBCCTModel] = Field(
        default=RGBCCTModel(r=255, g=0, b=0, cw=0, ww=0)
    )
    secondary: Union["AnimationModel", RGBCCTModel] = Field(
        default=RGBCCTModel(r=0, g=255, b=0, cw=0, ww=0)
    )


class PaintParams(BaseModel):
    """Parameters for the paint animation."""

    primary: Union["AnimationModel", RGBCCTModel] = Field(
        default=RGBCCTModel(r=255, g=0, b=0, cw=0, ww=0)
    )
    secondary: Union["AnimationModel", RGBCCTModel] = Field(
        default=RGBCCTModel(r=0, g=0, b=0, cw=0, ww=0)
    )
    radius: float = Field(default=150, ge=0)
    persistence: float = Field(default=2.0, ge=0)


class LinearRainbowParams(BaseModel):
    """Parameters for the linear_rainbow animation."""

    direction: Literal["x", "y"] = "x"
    speed: float = Field(default=0.1, ge=0)
    spread: float = Field(default=3.0, ge=0)


class SmoothParams(BaseModel):
    """Parameters for the smooth animation."""

    animation: Union["AnimationModel", RGBCCTModel] = Field(
        default=RGBCCTModel(r=255, g=0, b=0, cw=0, ww=0)
    )
    smoothing: float = Field(default=0.5, ge=0.0, le=1.0)


class PlasmaParams(BaseModel):
    """Parameters for the plasma animation."""

    speed: float = Field(default=0.5, ge=0)
    scale: float = Field(default=0.05, ge=0)


class ProximityParams(BaseModel):
    """Parameters for the proximity animation."""

    primary: Union["AnimationModel", RGBCCTModel] = Field(
        default=RGBCCTModel(r=255, g=255, b=255, cw=0, ww=0)
    )
    secondary: Union["AnimationModel", RGBCCTModel] = Field(
        default=RGBCCTModel(r=0, g=0, b=0, cw=0, ww=0)
    )
    x: float = 0.0
    y: float = 0.0
    radius: float = Field(default=200.0, ge=0)


class ProximitySpeedParams(BaseModel):
    """Parameters for the proximity_speed animation."""

    animation: Union["AnimationModel", RGBCCTModel] = Field(
        default=RGBCCTModel(r=255, g=255, b=255, cw=0, ww=0)
    )
    x: float = 0.0
    y: float = 0.0
    radius: float = Field(default=200.0, ge=0)
    multiplier: float = Field(default=1.0, ge=0)
    mode: Literal["speed up", "slow down"] = "speed up"
    proximity_factor: float = Field(default=0.5, ge=0.0, le=1.0)


class SparkleParams(BaseModel):
    """Parameters for the sparkle animation."""

    density: float = Field(default=0.1, ge=0.0, le=1.0)
    speed: float = Field(default=20.0, ge=0)


class NorthernLightsParams(BaseModel):
    """Parameters for the northern lights animation."""

    speed: float = Field(default=0.5, ge=0)
    intensity: float = Field(default=0.8, ge=0, le=1.0)


class LightningStormParams(BaseModel):
    """Parameters for the lightning storm animation."""

    frequency: float = Field(default=0.02, ge=0, le=1)
    base_brightness: float = Field(default=0.00, ge=0, le=1)


class PersistParams(BaseModel):
    """Parameters for the persist animation."""

    animation: Union["AnimationModel", RGBCCTModel] = Field(
        default=RGBCCTModel(r=255, g=0, b=0, cw=0, ww=0)
    )
    duration: float = Field(default=2.0, ge=0.0)


class DayOfWeekParams(BaseModel):
    """Parameters for the day_of_week animation."""

    monday: Union["AnimationModel", RGBCCTModel] = Field(
        default=RGBCCTModel(r=0, g=0, b=0, cw=0, ww=0)
    )
    tuesday: Union["AnimationModel", RGBCCTModel] = Field(
        default=RGBCCTModel(r=0, g=0, b=0, cw=0, ww=0)
    )
    wednesday: Union["AnimationModel", RGBCCTModel] = Field(
        default=RGBCCTModel(r=0, g=0, b=0, cw=0, ww=0)
    )
    thursday: Union["AnimationModel", RGBCCTModel] = Field(
        default=RGBCCTModel(r=0, g=0, b=0, cw=0, ww=0)
    )
    friday: Union["AnimationModel", RGBCCTModel] = Field(
        default=RGBCCTModel(r=0, g=0, b=0, cw=0, ww=0)
    )
    saturday: Union["AnimationModel", RGBCCTModel] = Field(
        default=RGBCCTModel(r=0, g=0, b=0, cw=0, ww=0)
    )
    sunday: Union["AnimationModel", RGBCCTModel] = Field(
        default=RGBCCTModel(r=0, g=0, b=0, cw=0, ww=0)
    )


class ExponentialAtParams(BaseModel):
    """Parameters for the exponential_at animation."""

    primary: Union["AnimationModel", RGBCCTModel] = Field(
        default=RGBCCTModel(r=255, g=0, b=0, cw=0, ww=0)
    )
    secondary: Union["AnimationModel", RGBCCTModel] = Field(
        default=RGBCCTModel(r=0, g=255, b=0, cw=0, ww=0)
    )
    x: float = 0.0
    y: float = 0.0
    radius: float = Field(default=150, ge=0)


class ExtrapolateParams(BaseModel):
    """Parameters for the extrapolate animation."""

    animation: Union["AnimationModel", RGBCCTModel] = Field(
        default=RGBCCTModel(r=255, g=255, b=255, cw=0, ww=0)
    )
    latency: float = Field(default=0.0)


class StripAssignmentParams(BaseModel):
    """Parameters for one strip assignment of the by_strip animation."""

    strip: int
    animation: Union["AnimationModel", RGBCCTModel]


class StripAssignmentWrapper(BaseModel):
    """Wrapper for one strip assignment of the by_strip animation."""

    strip_assignment: StripAssignmentParams = Field(..., title="Strip Assignment")

    model_config = ConfigDict(extra="forbid")


class ByStripParams(BaseModel):
    """Parameters for the by_strip animation."""

    assignments: list[StripAssignmentWrapper] = Field(default_factory=list)
    default: Union["AnimationModel", RGBCCTModel] = Field(
        default=RGBCCTModel(r=0, g=0, b=0, cw=0, ww=0)
    )


class PresetParams(BaseModel):
    """Parameters for the preset animation."""

    name: str = Field(..., description="Name of the preset to load.")


class AlternateAnimation(BaseModel):
    """Wrapper for the alternate animation."""

    alternate: AlternateParams = Field(
        ...,
        title="Alternate (Meta)",
        description="Alternates between multiple animations over time.",
    )

    model_config = ConfigDict(extra="forbid")


class FireAnimation(BaseModel):
    """Wrapper for the fire animation."""

    fire: FireParams = Field(
        ..., title="Fire", description="Simulates a flickering fire effect."
    )

    model_config = ConfigDict(extra="forbid")


class RainbowAnimation(BaseModel):
    """Wrapper for the rainbow animation."""

    rainbow: RainbowParams = Field(
        ..., title="Rainbow", description="A moving rainbow gradient across the floor."
    )

    model_config = ConfigDict(extra="forbid")


class StaticAnimation(BaseModel):
    """Wrapper for the static animation."""

    static: StaticParams = Field(
        ..., title="Static Color", description="Displays a single static color."
    )

    model_config = ConfigDict(extra="forbid")


class StroboAnimation(BaseModel):
    """Wrapper for the strobo animation."""

    strobo: StroboParams = Field(
        ..., title="Stroboscope", description="Flashes colors rapidly."
    )

    model_config = ConfigDict(extra="forbid")


class SwingAnimation(BaseModel):
    """Wrapper for the swing animation."""

    swing: SwingParams = Field(
        ...,
        title="Swing",
        description="A smooth swinging movement back and forth along an axis.",
    )

    model_config = ConfigDict(extra="forbid")


class Theater_chaseAnimation(BaseModel):
    """Wrapper for the theater_chase animation."""

    theater_chase: Theater_chaseParams = Field(
        ...,
        title="Theater Chase",
        description="A classic theater-style chasing lights effect.",
    )

    model_config = ConfigDict(extra="forbid")


class WaveAnimation(BaseModel):
    """Wrapper for the wave animation."""

    wave: WaveParams = Field(
        ...,
        title="Wave",
        description="Multiple sine waves interfering with each other.",
    )

    model_config = ConfigDict(extra="forbid")


class DotAnimation(BaseModel):
    """Wrapper for the dot animation."""

    dot: DotParams = Field(
        ...,
        title="Dot (Responsive)",
        description="Lights up area around detected objects.",
    )

    model_config = ConfigDict(extra="forbid")


class ExponentialAnimation(BaseModel):
    """Wrapper for the exponential animation."""

    exponential: ExponentialParams = Field(
        ...,
        title="Exponential (Responsive)",
        description="Exponential falloff brightness based on object proximity.",
    )

    model_config = ConfigDict(extra="forbid")


class OffAnimation(BaseModel):
    """Wrapper for the off animation."""

    off: OffParams = Field(..., title="Off", description="Turns all LEDs off.")

    model_config = ConfigDict(extra="forbid")


class IdleAnimation(BaseModel):
    """Wrapper for the idle animation."""

    idle: IdleParams = Field(
        ...,
        title="Idle Switch (Meta)",
        description="Switches between idle and active animations based on presence.",
    )

    model_config = ConfigDict(extra="forbid")


class BlendAnimation(BaseModel):
    """Wrapper for the blend animation."""

    blend: BlendParams = Field(
        ..., title="Blend (Meta)", description="Blends multiple animations together."
    )

    model_config = ConfigDict(extra="forbid")


class RaveAnimation(BaseModel):
    """Wrapper for the rave animation."""

    rave: RaveParams = Field(
        ..., title="Rave", description="High-energy intense light show."
    )

    model_config = ConfigDict(extra="forbid")


class ScheduleAnimation(BaseModel):
    """Wrapper for the schedule animation."""

    schedule: ScheduleParams = Field(
        ...,
        title="Schedule (Meta)",
        description="Runs different animations based on the time of day.",
    )

    model_config = ConfigDict(extra="forbid")


class PaintAnimation(BaseModel):
    """Wrapper for the paint animation."""

    paint: PaintParams = Field(
        ...,
        title="Paint (Responsive)",
        description="Draws trails that persist behind moving objects.",
    )

    model_config = ConfigDict(extra="forbid")


class LinearRainbowAnimation(BaseModel):
    """Wrapper for the linear_rainbow animation."""

    linear_rainbow: LinearRainbowParams = Field(
        ..., title="Linear Rainbow", description="A rainbow moving in a straight line."
    )

    model_config = ConfigDict(extra="forbid")


class SmoothAnimation(BaseModel):
    """Wrapper for the smooth animation."""

    smooth: SmoothParams = Field(
        ...,
        title="Smooth (Meta)",
        description="Smooths the output of another animation over time.",
    )

    model_config = ConfigDict(extra="forbid")


class PlasmaAnimation(BaseModel):
    """Wrapper for the plasma animation."""

    plasma: PlasmaParams = Field(
        ...,
        title="Plasma",
        description="Generates a classic, smoothly shifting plasma effect.",
    )

    model_config = ConfigDict(extra="forbid")


class ProximityAnimation(BaseModel):
    """Wrapper for the proximity animation."""

    proximity: ProximityParams = Field(
        ...,
        title="Proximity to Intensity (Responsive)",
        description="Blends animations based on object distance to a point.",
    )

    model_config = ConfigDict(extra="forbid")


class ProximitySpeedAnimation(BaseModel):
    """Wrapper for the proximity_speed animation."""

    proximity_speed: ProximitySpeedParams = Field(
        ...,
        title="Proximity to Speed (Responsive)",
        description=(
            "Increases the speed of the animation based on the distance to the "
            "target point."
        ),
    )

    model_config = ConfigDict(extra="forbid")


class SparkleAnimation(BaseModel):
    """Wrapper for the sparkle animation."""

    sparkle: SparkleParams = Field(
        ...,
        title="Sparkle",
        description="Creates a field of randomly twinkling colored pixels.",
    )

    model_config = ConfigDict(extra="forbid")


class NorthernLightsAnimation(BaseModel):
    """Wrapper for the northern lights animation."""

    northern_lights: NorthernLightsParams = Field(
        ...,
        title="Northern Lights",
        description="A flowing animation with green, teal, and purple colors.",
    )

    model_config = ConfigDict(extra="forbid")


class LightningStormAnimation(BaseModel):
    """Wrapper for the lightning storm animation."""

    lightning_storm: LightningStormParams = Field(
        ...,
        title="Lightning Storm",
        description="Occasional bright flashes like a lightning storm.",
    )

    model_config = ConfigDict(extra="forbid")


class PersistAnimation(BaseModel):
    """Wrapper for the persist animation."""

    persist: PersistParams = Field(
        ...,
        title="Persist (Meta/Responsive)",
        description="Keeps objects alive for a sub-animation after they disappear.",
    )

    model_config = ConfigDict(extra="forbid")


class DayOfWeekAnimation(BaseModel):
    """Wrapper for the day_of_week animation."""

    day_of_week: DayOfWeekParams = Field(
        ...,
        title="Day of Week (Meta)",
        description="Schedule different animations for each day of the week.",
    )

    model_config = ConfigDict(extra="forbid")


class ExponentialAtAnimation(BaseModel):
    """Wrapper for the exponential_at animation."""

    exponential_at: ExponentialAtParams = Field(
        ...,
        title="Exponential At",
        description=(
            "Exponential falloff brightness based on proximity to a fixed point."
        ),
    )

    model_config = ConfigDict(extra="forbid")


class ExtrapolateAnimation(BaseModel):
    """Wrapper for the extrapolate animation."""

    extrapolate: ExtrapolateParams = Field(
        ...,
        title="Extrapolate (Meta/Responsive)",
        description="Extrapolates object positions to compensate for latency.",
    )

    model_config = ConfigDict(extra="forbid")


class ByStripAnimation(BaseModel):
    """Wrapper for the by_strip animation."""

    by_strip: ByStripParams = Field(
        ...,
        title="By Strip (Meta)",
        description="Assign different animations to specific LED strips.",
    )

    model_config = ConfigDict(extra="forbid")


class PresetAnimation(BaseModel):
    """Wrapper for the preset animation."""

    preset: Union[PresetParams, str] = Field(
        ...,
        title="Preset",
        description="Loads an existing preset.",
    )

    model_config = ConfigDict(extra="forbid")


AnimationModel = Union[
    AlternateAnimation,
    FireAnimation,
    RainbowAnimation,
    StaticAnimation,
    StroboAnimation,
    SwingAnimation,
    Theater_chaseAnimation,
    WaveAnimation,
    DotAnimation,
    ExponentialAnimation,
    OffAnimation,
    IdleAnimation,
    BlendAnimation,
    RaveAnimation,
    ScheduleAnimation,
    PaintAnimation,
    LinearRainbowAnimation,
    SmoothAnimation,
    PlasmaAnimation,
    SparkleAnimation,
    NorthernLightsAnimation,
    LightningStormAnimation,
    ProximityAnimation,
    ProximitySpeedAnimation,
    PersistAnimation,
    DayOfWeekAnimation,
    ExponentialAtAnimation,
    ExtrapolateAnimation,
    ByStripAnimation,
    PresetAnimation,
]

DayOfWeekParams.model_rebuild()
ExponentialAtParams.model_rebuild()
ExtrapolateParams.model_rebuild()
ByStripParams.model_rebuild()
StripAssignmentParams.model_rebuild()
AlternateParams.model_rebuild()
FireParams.model_rebuild()
RainbowParams.model_rebuild()
StaticParams.model_rebuild()
StroboParams.model_rebuild()
SwingParams.model_rebuild()
Theater_chaseParams.model_rebuild()
WaveParams.model_rebuild()
DotParams.model_rebuild()
ExponentialParams.model_rebuild()
OffParams.model_rebuild()
IdleParams.model_rebuild()
BlendParams.model_rebuild()
RaveParams.model_rebuild()
ScheduleParams.model_rebuild()
PaintParams.model_rebuild()
LinearRainbowParams.model_rebuild()
SmoothParams.model_rebuild()
PlasmaParams.model_rebuild()
SparkleParams.model_rebuild()
NorthernLightsParams.model_rebuild()
LightningStormParams.model_rebuild()
ProximityParams.model_rebuild()
ProximitySpeedParams.model_rebuild()
PersistParams.model_rebuild()
