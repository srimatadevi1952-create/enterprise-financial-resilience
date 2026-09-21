# M22 Console Versions

Both design directions are retained in the repository. The selected dashboard direction is **V1 — Editorial globe concept**.

## V1 — Editorial globe concept

- Status: **Selected dashboard design**
- Current Live Monitor artifact: [`assets/m22-operating-modes/01-live-monitor-authorized-view.png`](assets/m22-operating-modes/01-live-monitor-authorized-view.png)
- Current Simulation Lab artifact: [`assets/m22-operating-modes/02-simulation-lab-private-collaboration.png`](assets/m22-operating-modes/02-simulation-lab-private-collaboration.png)
- Stable dashboard foundation: [`assets/m22-console-editorial-concept-v1.8-stable-baseline.png`](assets/m22-console-editorial-concept-v1.8-stable-baseline.png)
- Active-stress foundation: [`assets/m22-console-editorial-concept-v1.7-bowtie-active-severity.png`](assets/m22-console-editorial-concept-v1.7-bowtie-active-severity.png)
- Previous revision: [`assets/m22-console-editorial-concept-v1.6-unified-matrix-core-gradient.png`](assets/m22-console-editorial-concept-v1.6-unified-matrix-core-gradient.png)
- Previous revision: [`assets/m22-console-editorial-concept-v1.5-single-state-core-temperature.png`](assets/m22-console-editorial-concept-v1.5-single-state-core-temperature.png)
- Previous revision: [`assets/m22-console-editorial-concept-v1.4-core-heatmap.png`](assets/m22-console-editorial-concept-v1.4-core-heatmap.png)
- Previous revision: [`assets/m22-console-editorial-concept-v1.3-enterprise-environment.png`](assets/m22-console-editorial-concept-v1.3-enterprise-environment.png)
- Previous revision: [`assets/m22-console-editorial-concept-v1.2-operations-orbit.png`](assets/m22-console-editorial-concept-v1.2-operations-orbit.png)
- Previous revision: [`assets/m22-console-editorial-concept-v1.1-operations.png`](assets/m22-console-editorial-concept-v1.1-operations.png)
- Original artifact: [`assets/m22-console-editorial-concept.png`](assets/m22-console-editorial-concept.png)
- Git tag: `m22-globe-concept-v1`
- Preserves the earlier central-globe composition, orbital geometry, warm paper surface, graphite texture, and burnt-orange operator-console language.
- Revision V1.1 replaces input channel `03 RESILIENCE` with `03 OPERATIONS`. Enterprise resilience remains the calculated `87/100` outcome.
- Revision V1.2 also replaces the `RESILIENCE` orbital input label surrounding the enterprise core with `OPERATIONS`, completing the input/outcome distinction.
- Revision V1.3 separates the model into an inner-enterprise orbit for Capital, Liquidity and Operations and an external-environment orbit for Regulation, Merchants and Countries & Corridors. A compact legend distinguishes internal conditions, external forces, management interventions and calculated outcomes.
- Revision V1.4 turns the Enterprise Core into a dynamic Probability × Impact heat map. Burnt-orange hotspots, amber exposure zones, teal recovery zones and graphite stable regions update with scenario state and timeline playback.
- Revision V1.5 supersedes the V1.4 multizone treatment. The matrix and Enterprise Core now show the same consolidated Probability × Impact state: one active matrix colour and one matching uniform core colour at any time.
- Revision V1.6 removes the redundant core-temperature panel. Matrix-circle area and a continuous pale-yellow-to-deep-orange gradient both encode the `0–10 × 0–10` Probability × Impact product; the core uses the exact colour of the active matrix point.
- Revision V1.7 applies the shared severity palette to the Payment Disruption BowTie. Inactive attributes and paths remain black; only active elements change from pale yellow to deep orange according to their individual severity.
- Revision V1.8 establishes the stable baseline: at `0,0`, the core returns to its original graphite appearance, the matrix shows a graphite origin marker and all Payment Disruption attributes are inactive black. Risk colour begins only above zero.
- Revision V1.9 adds a persistent mode control, authorization status and isolated collaboration controls. Live Monitor remains the default read-only mode; Simulation Lab is privately enabled only after an individual authorization check.

## V2 — Interactive world-map console

- Status: Alternate prototype retained for reference
- Artifact: [`m22-interactive-world-console.html`](m22-interactive-world-console.html)
- Replaces the globe with a projected world map while retaining the V1 visual grammar.
- Adds selectable countries and corridors, live scenario controls, calculated metrics, scenario presets, and animated simulation playback.

V1 is the approved visual and interaction direction for the production dashboard. Its globe-centered composition will guide the next implementation stage. V2 remains available as a source for reusable map and scenario-control interactions.

The six channel-specific popup concepts and their interaction rules are recorded in the [M22 Control Popup UX/UI Design](M22_CONTROL_POPUP_UX_DESIGN.md).

The Live Monitor and authorised private Simulation Lab isolation, authorization and sharing rules are defined in [M22 Operating Modes, Authorization and Collaboration](M22_OPERATING_MODES_AUTHORIZATION_COLLABORATION.md).
