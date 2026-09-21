# M22 Enterprise Core Temperature Behaviour — V1.5 Superseded

This discrete teal–amber–orange model was superseded by the continuous pale-yellow-to-deep-orange matrix and core model in [M22 Enterprise Core Temperature Behaviour](M22_CORE_TEMPERATURE_BEHAVIOR.md). It is retained only as a version-history record.

**Visual foundation:** `m22-console-editorial-concept-v1.5-single-state-core-temperature`

**Purpose:** Present the enterprise's consolidated Probability × Impact condition as one colour state on the Enterprise Core.

## Single-state principle

The Probability × Impact matrix and the Enterprise Core show the same calculated state through two different representations:

- the matrix shows the state's analytical position;
- the core shows the state's immediate visual temperature.

The core displays exactly one state and one colour at a time. It never shows simultaneous multicolour zones.

`core_temperature(t) = aggregate_probability(t) × aggregate_impact(t)`

The aggregation method and threshold version must be visible and recorded with the simulation run.

## Shared colour tokens

| State | Matrix dot | Enterprise Core |
|---|---|---|
| Low | Restrained teal | Uniform restrained teal texture |
| Medium | Muted amber | Uniform muted amber texture |
| High | Burnt orange | Uniform burnt-orange texture |
| Stable / no active risk | Graphite | Uniform graphite texture |

The active matrix dot carries a visible selection ring. Its colour must exactly match the core. Tonal variation is allowed only for spherical light, shadow and material texture; it cannot introduce another state colour.

Colour is supported by the state name, numeric Probability × Impact score, selection ring and optional texture pattern so meaning is not dependent on colour perception.

## Dynamic behaviour

- Changing manipulated variables updates a preview matrix position and preview core temperature together.
- `APPLY TO DRAFT` stores the proposed state without running the simulation.
- `RUN` updates both representations at every simulation time step.
- `PAUSE` freezes the matrix and core at the same time step.
- Timeline scrubbing reconstructs the matched matrix position and core colour.
- Recovery moves the state through the defined bands, for example High → Medium → Low → Stable.
- Transitions are restrained and honour reduced-motion settings.

The matrix and core must never disagree. If either representation cannot be calculated, both display `STATE UNAVAILABLE` rather than showing stale or contradictory values.

## Detail and causality

The single core temperature is an enterprise-level summary. Detail remains available through the six controls, parameter decks, orbit connectors, BowTie diagram, trends and evidence views.

Selecting the active matrix dot or the core reveals:

- aggregate probability and impact;
- active state and threshold;
- contributing internal conditions and external forces;
- dominant manipulated variables;
- affected obligations, merchants, countries, corridors and systems;
- confidence and data-quality grade;
- Enterprise Resilience Index effect.

## Aggregation

The approved enterprise state can be calculated using a configured aggregation policy such as dominant risk, weighted portfolio score or board-approved composite. Only one policy is active for a run. The interface identifies that policy and provides drill-down to its components without rendering multiple colours on the core.

## Evidence and audit

Every state change records:

- scenario, run and time-step identifiers;
- aggregate probability, aggregate impact and product;
- aggregation method;
- threshold and colour-token version;
- active matrix cell;
- core state and colour token;
- contributing risks, variables and evidence;
- confidence and data-quality grade.

The core temperature is a read-only result. Selecting or recolouring the core cannot modify the simulation.
