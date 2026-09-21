# M22 Enterprise Core Heat-Map Behaviour — V1.4 Superseded

This multizone model was superseded by the single-state model in [M22 Enterprise Core Temperature Behaviour](M22_CORE_TEMPERATURE_BEHAVIOR.md). It is retained only as a version-history record.

**Visual foundation:** `m22-console-editorial-concept-v1.4-core-heatmap`

**Purpose:** Reflect Probability × Impact results directly on the Enterprise Core during scenario editing and simulation playback.

## Core principle

The Enterprise Core is a live analytical surface. Its colour zones represent the current probability-and-impact condition of the enterprise rather than decoration or geography.

For each risk observation at time `t`:

`core_heat(t) = normalized_probability(t) × normalized_impact(t)`

Exposure, concentration and confidence remain visible as supporting attributes and can influence zone size, opacity and certainty treatment, but they do not replace the Probability × Impact basis.

## Visual encoding

| Condition | Core treatment |
|---|---|
| Stable or unaffected | Graphite texture |
| Low Probability × Impact or recovery capacity | Restrained teal |
| Medium Probability × Impact | Muted amber |
| High Probability × Impact | Burnt orange |
| Uncertain or low-confidence result | Hatched or stippled boundary with confidence label |

Colour must always be accompanied by a label, numeric value, pattern or focus state. The display cannot rely on colour perception alone.

## Spatial mapping

Heat zones are assigned to enterprise domains and affected assets, not to geographic continents. A deterministic zone map keeps the same domain in the same core region between runs so users can compare scenarios reliably.

- Capital effects occupy the capital sector.
- Liquidity effects occupy the liquidity sector.
- Operations effects occupy the operations sector.
- Regulation, Merchants and Countries & Corridors project their consequences into the affected internal sector through visible connectors.
- Cross-domain consequences can span sectors and display a propagation boundary.

The high/high cell in the Probability × Impact matrix must correspond to the strongest burnt-orange zone on the core. Medium and low cells create proportionate amber and teal zones.

## Dynamic behaviour

- Moving any manipulated variable updates a preview heat layer without running the scenario.
- `APPLY TO DRAFT` records the proposed values and retains the preview state.
- `RUN` animates heat-zone emergence, propagation, peak condition and recovery along the scenario timeline.
- `PAUSE` freezes the core at the selected time.
- Timeline scrubbing reconstructs the heat state for that period.
- Comparing scenarios can use an outline, split-core or difference layer to show changed zones.
- Recovery actions cause high-risk zones to contract or transition through amber toward teal and graphite.
- Changes use restrained transitions and respect reduced-motion preferences.

## Cross-highlighting

Selecting a matrix cell or core zone highlights all connected evidence:

- probability and impact values;
- contributing manipulated variables;
- internal domain and external source;
- BowTie threat, control and consequence;
- affected merchant, country, corridor, system or obligation;
- capital, liquidity and recovery trajectory effects;
- resulting Enterprise Resilience Index delta.

Selecting a core zone filters the other dashboard views to the same risk. Hover and keyboard focus display the zone name, Probability × Impact score, confidence, affected value and time.

## Aggregation

When multiple risks affect the same core sector, the interface provides three approved views:

1. **Dominant risk:** displays the highest Probability × Impact result.
2. **Composite heat:** displays the configured weighted aggregate and identifies its components.
3. **Layered risks:** allows individual risks to be toggled without changing the scenario.

The active aggregation method must always be visible and recorded with the run.

## Evidence and audit

Every rendered heat state records:

- scenario and run identifiers;
- time step;
- risk and zone identifiers;
- probability, impact and calculated heat;
- aggregation method;
- contributing variables and evidence references;
- confidence and data-quality grade;
- colour band and threshold version.

The core heat map remains a read-only visual consequence of simulation state. Directly painting or recolouring the core cannot change a risk value.
