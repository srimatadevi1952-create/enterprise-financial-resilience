# M22 Visualization Tool Design

## Purpose

The visualization tool will make the Enterprise Financial Resilience and Control Operating System understandable to executives, risk analysts, compliance teams, and operations users. It will combine a 3D enterprise network with established risk visualizations so a user can see what is exposed, why it is exposed, how stress propagates, and which intervention changes the outcome.

## User modes

### CEO and Board mode

Shows resilience status, scenario impact, capital and liquidity, recovery outcome, country and corridor exposure, confidence, unresolved issues, and the decision required. It uses plain language and hides implementation detail.

### Risk and Compliance mode

Shows risk scores, heat maps, BowTie diagrams, regulatory regimes, forensic signals, merchant concentration, corridor conditions, and evidence references.

### Operations mode

Shows settlement queues, feed quality, gateway states, reconciliation exceptions, alerts, retries, and run controls.

### Exploration mode

Allows a user to change scenario inputs, run a time-step simulation, compare branches, pause propagation, and inspect the evidence behind each result.

## Main workspace

The main view is a 3D enterprise network. The enterprise is central, with merchants, gateways, banks, corridors, and country nodes arranged in a navigable scene. Animated links represent settlement flows. Node size represents exposure. Node color represents condition class. Link thickness represents value or volume. A timeline controls playback of stress propagation and recovery.

The 3D scene is an explanatory network, not a geographic claim. A separate geographic view uses country and corridor geometry when location matters.

## Risk visualization surfaces

### Heat map

Rows represent merchants, corridors, countries, or risk dimensions. Columns represent probability, impact, exposure, liquidity, compliance, and recovery time. Colors must be paired with labels and numeric values so the display remains usable without color perception.

### BowTie view

The center event is the selected failure, such as settlement delay, gateway outage, regulatory restriction, or liquidity shortfall. The left side shows threats and preventive controls. The right side shows consequences, recovery controls, and decision actions. Each node links to evidence.

### Trend and trajectory charts

Time-series views show stability grade, fragility index, shock absorption capacity, capital compression, liquidity balance, and recovery progress. Scenario lines share a common scale so baseline, stress, control, and intervention can be compared directly.

### Capital and liquidity waterfall

Waterfalls show starting capital or liquidity, stress losses, reserve draws, funding inflows, recovery inflows, and restored balance.

### Geographic corridor view

Country and corridor maps show currency, cut-off, regulatory, compliance, FX, and settlement conditions. Corridor direction is explicit because the reverse route can have different risk.

## Scenario control panel

Controls are grouped into operational, regulatory, market, and recovery inputs:

- Settlement delay
- Gateway outage and retry rate
- Inflow and outflow shocks
- FX shock
- Reserve requirement
- Compliance review rate
- Corridor restriction
- Merchant failure rate
- Funding capacity
- Intervention selection

Every change creates a new immutable scenario draft. The user can run it, compare it with a selected branch, or discard it. The tool must display the active assumptions before showing results.

## Results panel

The results panel reports completion, held obligations, exposure, liquidity, capital, stability, fragility, recovery time, enterprise class, alerts, and confidence. Each number has an evidence link to the run, feed, metric definition, observation, or decision record that supports it.

## Interaction model

Selecting a node, corridor, risk cell, BowTie event, chart point, or alert filters every other view to the same subject. A scenario can be scrubbed through time, paused at a propagation wave, and compared with baseline or control. The interface must support keyboard navigation, text alternatives, visible labels, and a non-3D two-dimensional fallback.

## Data and safety boundary

The first implementation uses V2 synthetic and test data. The visual layer reads run manifests, observations, metrics, classifications, capital and liquidity trajectories, risk scores, regulatory impacts, and board-pack evidence. It cannot write financial actions. Shadow data remains read-only. Live intervention controls are outside the visualization boundary.

## Build sequence

1. Create a read-only scenario data API and normalized visualization payload.
2. Build the CEO and analyst 2D surfaces first.
3. Add the 3D network scene and timeline playback.
4. Add heat maps, BowTie diagrams, trend charts, waterfalls, and maps.
5. Add scenario controls and branch comparison.
6. Add evidence drill-down and exportable executive packs.
7. Validate against M21 shadow evidence before any production connection.

## Acceptance criteria

- A user can understand the active scenario and its assumptions in under one minute.
- Every visual metric traces to stored evidence.
- Baseline, stress, control, intervention, and systemic collapse can be compared.
- Scenario changes do not mutate historical runs.
- The 3D view and 2D fallback show the same values.
- The interface remains read-only and cannot initiate financial actions.
- CEO, analyst, and operations modes expose the appropriate level of detail.
