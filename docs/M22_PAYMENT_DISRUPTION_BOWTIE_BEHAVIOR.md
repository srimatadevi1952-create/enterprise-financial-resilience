# M22 Payment Disruption BowTie Behaviour

**Visual foundation:** `m22-console-editorial-concept-v1.7-bowtie-active-severity`

## Purpose

The Payment Disruption BowTie explains which threats are active, how they combine into the central disruption event, and which consequences have propagated. Activity and severity are distinct attributes.

## Inactive state

Inactive threats, consequences and path segments remain graphite black. They do not receive a risk colour, fade to grey or disappear. This preserves the complete causal structure while clearly separating inactive attributes from active ones.

## Active state

Only active elements use colour. Each active threat and consequence receives a shade based on its own severity from `0–10`:

- low severity: pale yellow;
- medium severity: golden amber;
- elevated severity: orange;
- high severity: deep burnt orange.

The palette is identical to the Probability × Impact matrix. No separate BowTie colour legend is required.

## Path treatment

- A threat-to-event path changes colour only when that threat is active.
- Its shade matches the active threat severity.
- An event-to-consequence path changes colour only when that consequence has propagated.
- Its shade matches the consequence severity.
- Inactive paths remain black even when an adjacent path is active.
- Path thickness and node geometry remain constant; severity is encoded by colour only.

## Central event

The Payment Disruption circle represents the combined state of active threats after preventive and detective control effects. It uses the same pale-yellow-to-deep-orange scale, based on the configured aggregate disruption severity. Its size remains fixed.

The central event is not automatically identical to the Enterprise Core state. The BowTie represents the selected Payment Disruption risk; the core represents the enterprise aggregate. When Payment Disruption is the sole or dominant risk, their colours may match.

## Dynamic behaviour

During simulation playback:

1. active threat nodes change from black to their severity colour;
2. their incoming paths change to the matching colour;
3. the central event updates to the aggregate disruption severity;
4. propagated consequence paths and nodes change from black to their individual severity colour;
5. mitigated or resolved attributes return to black when they become inactive.

Timeline scrubbing reconstructs the exact active set and severity shades for the selected time step.

## Interaction and evidence

Selecting an active or inactive attribute shows its status, severity, probability, impact, activation time, contributing variables, related controls, confidence and evidence. Keyboard focus and accessible descriptions communicate status and severity without depending on colour.

Every state change records the scenario, run, time step, attribute ID, active flag, severity, colour token, propagation path, contributing variables, controls, confidence and evidence references.
