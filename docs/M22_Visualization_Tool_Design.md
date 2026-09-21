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

The orbital model distinguishes two domains. The inner-enterprise ring contains Capital, Liquidity and Operations. The external-environment ring contains Regulation, Merchants and Countries & Corridors. Connections show how external shocks propagate into internal conditions and ultimately change the Enterprise Resilience Index. A visual legend differentiates internal conditions, external forces, management interventions and calculated outcomes.

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

## Operator console

The visualization is paired with a studio-style operator console inspired by a professional recording desk. The console is a second work surface below or beside the 3D scene. It exposes the model parameters in organized control strips while the 3D network, heat maps, BowTie, charts, and executive results update together.

### Console strips

The six master input channels are **Capital, Liquidity, Operations, Regulation, Merchants, and Corridors**. **Enterprise Resilience** is a calculated outcome that responds to these inputs and is displayed in the results area as the Enterprise Resilience Index.

The authoritative implementation inventory is the [M22 Manipulated Variable Register](M22_MANIPULATED_VARIABLE_REGISTER.md), with its machine-readable companion at `config/m22_manipulated_variables.csv`. It defines 220 variables across the six controls and distinguishes starting states, external shocks, behavioural assumptions, and management interventions.

- **Population:** merchants, transaction volume, currencies, gateways, countries, and corridor selection
- **Settlement:** delay hours, batch windows, retry rate, held-obligation policy, and reconciliation tolerance
- **Gateway:** outage percentage, latency, duplicate rate, retry behavior, and provider selection
- **Market:** FX shock, inflow shock, outflow surge, fee change, and funding cost
- **Regulatory:** reserve rate, review rate, restriction state, effective date, and remediation speed
- **Merchant risk:** merchant failure rate, concentration threshold, anomaly sensitivity, and exposure limit
- **Systemic cascade:** initial nodes, propagation rate, wave interval, liquidity threshold, and recovery capacity
- **Capital and liquidity:** starting capital, reserve draw, funding capacity, regeneration inflow, and recovery horizon
- **Intervention:** selected action, approval requirement, execution timing, release scope, and control comparison

Each strip has a value field, unit, range indicator, reset control, automation lane, and a small status meter. Controls are grouped by business meaning rather than by database table. Users can save a named scenario snapshot and compare it with baseline, stress, control, intervention, or systemic collapse.

### Master controls

The console has transport-style controls: Run, Pause, Step, Reset, Branch, Compare, and Commit Scenario. A time ruler shows the current simulation period and propagation wave. The operator can scrub to a specific event and inspect which controls changed the result.

Each channel opens a draggable parameter deck. The user can position the deck anywhere within the dashboard workspace, snap it to an edge or return it to its default channel-anchored position. Movement must support pointer, touch and keyboard input, preserve access to the title bar and safety status, and affect presentation only.

### Automation and what-if lanes

Every parameter can be constant, stepped, ramped, or scripted over time. For example, an operator can ramp an FX shock from 0% to 12%, delay a gateway by six hours, then apply an intervention at wave three. The console displays the active automation curves and the resulting 3D propagation.

### Live effect feedback

When a control changes, the console shows the delta before committing the scenario: obligations newly held, liquidity change, capital change, risk-band movement, metric change, recovery-time change, and confidence impact. The 3D scene highlights the affected nodes and links, the heat map updates its cells, and the BowTie view highlights the activated threat or control.

### Safety and reversibility

The console is simulation-only. It cannot initiate payments, modify a source ledger, or enable live intervention. Every run is immutable, versioned, and replay-safe. Reset returns to the last committed scenario. The production shadow mode disables all financial action controls and exposes only read-only observation parameters.

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
