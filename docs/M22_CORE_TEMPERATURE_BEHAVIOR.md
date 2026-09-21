# M22 Enterprise Core Temperature Behaviour

**Visual foundation:** `m22-console-editorial-concept-v1.6-unified-matrix-core-gradient`

**Purpose:** Make the Probability × Impact matrix and Enterprise Core two synchronized representations of the same consolidated state.

## Unified representation

The matrix is the analytical representation. The core is the immediate visual representation. A separate core-temperature panel is unnecessary and must not be displayed.

At time `t`:

`risk_score(t) = probability(t) × impact(t)`

Probability and impact each use a continuous scale from `0` to `10`; the resulting score ranges from `0` to `100`. The active matrix point and the entire textured Enterprise Core always use the same colour derived from this score.

## Matrix construction

The matrix uses Probability on the horizontal axis and Impact on the vertical axis. Both axes progress from Low through Medium to High and represent the continuous `0–10` domain.

The nine displayed points provide representative combinations:

| Impact \ Probability | Low | Medium | High |
|---|---|---|---|
| High | Low × High | Medium × High | High × High |
| Medium | Low × Medium | Medium × Medium | High × Medium |
| Low | Low × Low | Medium × Low | High × Low |

Symmetric products, such as Low × High and High × Low, must use equal size and equal shade.

## Size encoding

Circle area represents the combined Probability × Impact score. Because viewers perceive area rather than diameter, the radius uses square-root scaling:

`radius = minimum_radius + size_range × sqrt(risk_score / 100)`

The minimum radius keeps the `0,0` state discoverable. The maximum circle must remain inside its grid cell. The selection ring does not count toward encoded size.

## Colour encoding

The matrix uses one sequential palette only:

- minimum: very pale yellow;
- low: warm yellow;
- medium: golden amber;
- elevated: light to medium orange;
- maximum: deep burnt orange.

Colour is interpolated continuously from the normalized score. Teal, green, blue, grey and red are not used for Probability × Impact points. The active point has a fine selection ring, and the Enterprise Core uses its exact colour.

Tonal variation on the core is permitted only for spherical lighting and surface texture. It cannot introduce another state colour.

## Dynamic behaviour

- Manipulated-variable changes move the preview point and recolour the preview core together.
- `APPLY TO DRAFT` stores the proposed position without running the simulation.
- `RUN` updates point position, point size, point shade and core colour at each time step.
- `PAUSE` freezes both representations at the same time step.
- Timeline scrubbing reconstructs the synchronized state.
- Recovery causes the point to move toward the matrix origin while its circle becomes smaller and paler; the core changes to the identical shade.
- Transitions remain restrained and respect reduced-motion preferences.

The matrix and core must never disagree. If either cannot be calculated, both show `STATE UNAVAILABLE` rather than retaining stale values.

## Detail and accessibility

Selecting the active point or core reveals:

- Probability value from `0–10`;
- Impact value from `0–10`;
- calculated score from `0–100`;
- contributing internal conditions and external forces;
- dominant manipulated variables;
- confidence and data-quality grade;
- Enterprise Resilience Index effect.

Colour and size are supported by numeric values, axis position, focus treatment and an accessible state description.

## Evidence and audit

Every change records the scenario, run, time step, probability, impact, score, circle radius, colour value, active cell, aggregation method, contributing variables, evidence, confidence and palette version.

The core colour is a read-only simulation result. Selecting or recolouring the core cannot modify the scenario.
