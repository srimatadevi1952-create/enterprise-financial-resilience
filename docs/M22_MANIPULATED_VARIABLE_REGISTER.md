# M22 Manipulated Variable Register

**Status:** Approved modelling baseline  
**Dashboard control structure:** Capital, Liquidity, Operations, Regulation, Merchants, Countries & Corridors  
**Calculated outcome:** Enterprise Resilience Index

## 1. Modelling rule

The six dashboard controls are parameter groups rather than single inputs. The operator manipulates the variables below to construct a baseline, stress scenario, intervention, or recovery path. The simulation engine calculates resilience, losses, liquidity survival, capital adequacy, operational continuity, regulatory exposure, recovery time, and capital regeneration from those inputs.

Every variable must carry:

- parameter ID and definition;
- unit, currency and measurement basis;
- baseline, stressed value and intervention value;
- permitted minimum, maximum and validation rule;
- effective start, duration and recovery profile;
- time behaviour: constant, step, ramp, pulse, curve or stochastic;
- uncertainty distribution and confidence level;
- enterprise, entity, business unit, merchant, country and corridor scope;
- dependencies and correlation assumptions;
- source, owner, evidence date and data-quality grade;
- scenario version and audit history.

Variable types used below are **State** (starting condition), **Shock** (external or adverse change), **Behaviour** (model response assumption), and **Intervention** (management action).

## 2. Control 01 — Capital

| ID | Manipulated variable | Type | Typical unit |
|---|---|---|---|
| CAP-01 | Opening common equity | State | Currency |
| CAP-02 | Retained earnings | State | Currency |
| CAP-03 | Additional paid-in capital | State | Currency |
| CAP-04 | Regulatory or statutory capital, where applicable | State | Currency / ratio |
| CAP-05 | General and specific reserves | State | Currency |
| CAP-06 | Subordinated and loss-absorbing debt | State | Currency |
| CAP-07 | Total debt outstanding | State | Currency |
| CAP-08 | Debt maturity profile | State | Currency by period |
| CAP-09 | Leverage ratio | State | Ratio |
| CAP-10 | Covenant headroom | State | Currency / ratio |
| CAP-11 | Risk-weighted or economic-capital exposure | State | Currency |
| CAP-12 | Asset impairment rate | Shock | % |
| CAP-13 | Credit-loss severity | Shock | % / currency |
| CAP-14 | Market-value or valuation haircut | Shock | % |
| CAP-15 | Intangible or goodwill impairment | Shock | Currency / % |
| CAP-16 | Operational-loss charge | Shock | Currency |
| CAP-17 | Regulatory fine or legal-loss charge | Shock | Currency |
| CAP-18 | Tax-loss and deferred-tax recognition | Behaviour | Currency / % |
| CAP-19 | Earnings generation rate | Behaviour | Currency per period |
| CAP-20 | Dividend and distribution rate | Intervention | % / currency |
| CAP-21 | Share buyback or capital-return rate | Intervention | Currency |
| CAP-22 | New equity injection | Intervention | Currency / date |
| CAP-23 | Debt-to-equity conversion | Intervention | Currency / % |
| CAP-24 | Asset disposal proceeds and disposal haircut | Intervention | Currency / % |
| CAP-25 | Cost reduction retained as capital | Intervention | Currency per period |
| CAP-26 | Capital regeneration rate | Behaviour | Currency per period |
| CAP-27 | Target capital buffer | Intervention | Currency / ratio |
| CAP-28 | Capital-action execution delay | Behaviour | Days |

## 3. Control 02 — Liquidity

| ID | Manipulated variable | Type | Typical unit |
|---|---|---|---|
| LIQ-01 | Opening unrestricted cash | State | Currency |
| LIQ-02 | Restricted or trapped cash | State | Currency |
| LIQ-03 | Cash by legal entity, bank and currency | State | Currency |
| LIQ-04 | Minimum operating cash requirement | State | Currency |
| LIQ-05 | Daily customer or merchant inflows | Behaviour | Currency per day |
| LIQ-06 | Daily operating outflows | Behaviour | Currency per day |
| LIQ-07 | Receivable collection rate | Behaviour | % / days |
| LIQ-08 | Payable timing and payment deferral | Behaviour / intervention | Days / % |
| LIQ-09 | Settlement inflow delay | Shock | Hours / days |
| LIQ-10 | Settlement outflow acceleration | Shock | Hours / days |
| LIQ-11 | Deposit, customer-balance or merchant-balance runoff | Shock | % |
| LIQ-12 | Refund and chargeback cash demand | Shock | Currency / % |
| LIQ-13 | Margin-call and collateral demand | Shock | Currency |
| LIQ-14 | Debt-service requirement | State | Currency by period |
| LIQ-15 | Intraday liquidity requirement | Behaviour | Currency |
| LIQ-16 | Liquidity reserve size | State / intervention | Currency |
| LIQ-17 | Committed credit-facility capacity | State | Currency |
| LIQ-18 | Undrawn funding availability | State | Currency |
| LIQ-19 | Funding drawdown amount | Intervention | Currency |
| LIQ-20 | Funding drawdown delay | Behaviour | Hours / days |
| LIQ-21 | Funding interest rate and spread | Shock | Basis points |
| LIQ-22 | Refinancing availability | Shock | % / binary |
| LIQ-23 | Collateral availability | State | Currency |
| LIQ-24 | Collateral haircut | Shock | % |
| LIQ-25 | Asset monetisation capacity | Intervention | Currency per day |
| LIQ-26 | Asset-sale settlement delay | Behaviour | Days |
| LIQ-27 | FX liquidity requirement | Shock | Currency by denomination |
| LIQ-28 | Currency-conversion availability | Shock | % / binary |
| LIQ-29 | Emergency funding injection | Intervention | Currency / date |
| LIQ-30 | Cash-pooling and intercompany-transfer capacity | Intervention | Currency / % |
| LIQ-31 | Liquidity survival threshold | State | Days |
| LIQ-32 | Contingency funding-plan activation point | Intervention | Ratio / date |

## 4. Control 03 — Operations

| ID | Manipulated variable | Type | Typical unit |
|---|---|---|---|
| OPS-01 | Normal processing capacity | State | Transactions per period |
| OPS-02 | Available capacity under stress | Shock | % |
| OPS-03 | Transaction arrival rate | Behaviour | Transactions per second |
| OPS-04 | Peak-load multiplier | Shock | Multiple |
| OPS-05 | Processing latency | State / shock | Milliseconds / hours |
| OPS-06 | Transaction error or failure rate | Shock | % |
| OPS-07 | Backlog size | State | Transactions / currency |
| OPS-08 | Backlog clearance rate | Intervention | Transactions per period |
| OPS-09 | Critical-system availability | State / shock | % |
| OPS-10 | System outage duration | Shock | Minutes / hours |
| OPS-11 | Recovery time objective | State | Hours |
| OPS-12 | Recovery point objective and data-loss window | State | Minutes / hours |
| OPS-13 | Failover success probability | Behaviour | % |
| OPS-14 | Redundant capacity | State / intervention | % |
| OPS-15 | Infrastructure scaling rate and delay | Intervention | Capacity / minutes |
| OPS-16 | Network, cloud or data-centre degradation | Shock | % |
| OPS-17 | Cyberattack intensity | Shock | Index |
| OPS-18 | Cyber-control effectiveness | State / intervention | % |
| OPS-19 | Fraud-control availability | State / shock | % |
| OPS-20 | Data completeness | State / shock | % |
| OPS-21 | Data accuracy and integrity | State / shock | % |
| OPS-22 | Data-feed delay | Shock | Minutes / hours |
| OPS-23 | Reconciliation break rate | Shock | % / count |
| OPS-24 | Reconciliation clearance time | Behaviour / intervention | Hours |
| OPS-25 | Manual-processing capacity | State / intervention | Cases per day |
| OPS-26 | Workforce availability | Shock | % |
| OPS-27 | Workforce productivity | Behaviour | % |
| OPS-28 | Key-person dependency | State | Concentration index |
| OPS-29 | Facility availability | Shock | % |
| OPS-30 | Power and telecommunications availability | Shock | % |
| OPS-31 | Critical supplier availability | Shock | % |
| OPS-32 | Third-party service degradation | Shock | % |
| OPS-33 | Third-party recovery time | Behaviour | Hours / days |
| OPS-34 | Inventory or critical-resource cover | State | Days |
| OPS-35 | Business-continuity-plan effectiveness | State / intervention | % |
| OPS-36 | Incident detection time | Behaviour | Minutes / hours |
| OPS-37 | Incident containment time | Behaviour / intervention | Hours |
| OPS-38 | Crisis decision and escalation delay | Behaviour | Minutes / hours |
| OPS-39 | Recovery-resource allocation | Intervention | People / currency / capacity |
| OPS-40 | Physical hazard or extreme-weather disruption | Shock | Severity / duration |

## 5. Control 04 — Regulation

| ID | Manipulated variable | Type | Typical unit |
|---|---|---|---|
| REG-01 | Applicable jurisdictions and regulatory regimes | State | Set / count |
| REG-02 | Licence status and permitted activities | State / shock | Category / binary |
| REG-03 | New-rule effective date | Shock | Date |
| REG-04 | Regulatory transition period | Shock | Days / months |
| REG-05 | Minimum capital requirement | Shock | Currency / ratio |
| REG-06 | Minimum liquidity requirement | Shock | Currency / ratio |
| REG-07 | Reserve, safeguarding or segregation requirement | Shock | % / currency |
| REG-08 | Customer due-diligence threshold | Shock | Currency / risk score |
| REG-09 | Enhanced due-diligence rate | Shock | % |
| REG-10 | AML transaction-monitoring sensitivity | State / intervention | Threshold / score |
| REG-11 | Sanctions-screening sensitivity | State / intervention | Threshold / score |
| REG-12 | Sanctions, embargo or restricted-party scope | Shock | Set / severity |
| REG-13 | Suspicious-activity reporting threshold | Shock | Score / currency |
| REG-14 | Regulatory reporting frequency and deadline | Shock | Days / frequency |
| REG-15 | Data-retention period | Shock | Months / years |
| REG-16 | Data-localisation requirement | Shock | % / binary |
| REG-17 | Privacy and consent restriction | Shock | Severity / category |
| REG-18 | Consumer-protection obligation | Shock | Severity / cost |
| REG-19 | Pricing, interchange or fee cap | Shock | % / currency |
| REG-20 | Tax rate, withholding tax and digital levy | Shock | % |
| REG-21 | Tariff or customs obligation | Shock | % / currency |
| REG-22 | Regulatory review or approval delay | Behaviour | Days |
| REG-23 | Examination or enforcement probability | Behaviour | % |
| REG-24 | Fine and penalty severity | Shock | Currency / % |
| REG-25 | Remediation cost | Intervention | Currency |
| REG-26 | Compliance staffing and capacity | Intervention | FTE / cases per day |
| REG-27 | Compliance-control effectiveness | State / intervention | % |
| REG-28 | Legal interpretation uncertainty | Behaviour | Confidence / range |
| REG-29 | Regulatory divergence between jurisdictions | Shock | Index |
| REG-30 | Reporting, licence or control breach tolerance | Intervention | Threshold |
| REG-31 | Regulatory-capital or activity restriction | Shock | % / binary |
| REG-32 | Transition-policy and environmental compliance cost | Shock | Currency / % |

## 6. Control 05 — Merchants

| ID | Manipulated variable | Type | Typical unit |
|---|---|---|---|
| MER-01 | Active merchant population | State | Count |
| MER-02 | Merchant additions and attrition | Behaviour | Count / % per period |
| MER-03 | Transaction volume by merchant | State / behaviour | Count per period |
| MER-04 | Transaction value by merchant | State / behaviour | Currency per period |
| MER-05 | Average ticket size | Behaviour | Currency |
| MER-06 | Volume growth or contraction | Shock | % |
| MER-07 | Seasonal and event-driven volume multiplier | Behaviour | Multiple |
| MER-08 | Merchant sector or industry mix | State | % by sector |
| MER-09 | Merchant country and corridor mix | State | % by geography |
| MER-10 | Revenue contribution by merchant | State | Currency / % |
| MER-11 | Top-merchant concentration | State / shock | % / HHI |
| MER-12 | Sector concentration | State / shock | % / HHI |
| MER-13 | Geographic concentration | State / shock | % / HHI |
| MER-14 | Merchant credit score | State / shock | Score |
| MER-15 | Probability of merchant default | Shock | % |
| MER-16 | Loss given merchant default | Behaviour | % |
| MER-17 | Merchant financial-health deterioration | Shock | Score / % |
| MER-18 | Merchant fraud rate | Shock | % / basis points |
| MER-19 | Chargeback rate | Shock | % / basis points |
| MER-20 | Refund rate | Shock | % |
| MER-21 | Dispute rate and resolution time | Behaviour | % / days |
| MER-22 | Merchant reserve or holdback rate | State / intervention | % |
| MER-23 | Settlement delay by merchant tier | State / intervention | Days |
| MER-24 | Payout acceleration | Intervention | Hours / days |
| MER-25 | Exposure limit by merchant | Intervention | Currency |
| MER-26 | Collateral or guarantee coverage | State / intervention | Currency / % |
| MER-27 | Merchant onboarding rate | Behaviour / intervention | Count per period |
| MER-28 | KYC and underwriting acceptance threshold | Intervention | Score |
| MER-29 | Merchant monitoring sensitivity | Intervention | Threshold / score |
| MER-30 | Merchant suspension or offboarding threshold | Intervention | Score / binary |
| MER-31 | Merchant network contagion rate | Behaviour | % |
| MER-32 | Common-acquirer, gateway or bank dependency | State | % / count |
| MER-33 | Merchant operating interruption duration | Shock | Hours / days |
| MER-34 | Merchant recovery rate | Behaviour | % per period |
| MER-35 | Merchant fee and margin rate | State / intervention | % / basis points |
| MER-36 | Merchant support and remediation capacity | Intervention | Cases / currency per day |

## 7. Control 06 — Countries & Corridors

| ID | Manipulated variable | Type | Typical unit |
|---|---|---|---|
| COR-01 | Origin country | State | ISO country code |
| COR-02 | Destination country | State | ISO country code |
| COR-03 | Corridor direction | State | Direction |
| COR-04 | Origin and destination currency | State | ISO currency code |
| COR-05 | Transaction volume by corridor | State / behaviour | Count per period |
| COR-06 | Transaction value by corridor | State / behaviour | Currency per period |
| COR-07 | Corridor growth or contraction | Shock | % |
| COR-08 | Corridor concentration | State / shock | % / HHI |
| COR-09 | Country exposure limit | Intervention | Currency / % |
| COR-10 | Corridor exposure limit | Intervention | Currency / % |
| COR-11 | Sovereign credit risk | Shock | Rating / spread |
| COR-12 | Political-stability risk | Shock | Index |
| COR-13 | War, conflict or civil-unrest severity | Shock | Index / duration |
| COR-14 | Government-change or policy-reversal probability | Shock | % |
| COR-15 | Expropriation or nationalisation risk | Shock | % / severity |
| COR-16 | Sanctions and embargo severity | Shock | Index / binary |
| COR-17 | Trade restriction and tariff severity | Shock | % / index |
| COR-18 | Capital-control severity | Shock | Index / % trapped |
| COR-19 | Currency convertibility | Shock | % / binary |
| COR-20 | FX spot-rate movement | Shock | % |
| COR-21 | FX volatility | Shock | % annualised / period |
| COR-22 | FX spread and hedging cost | Shock | Basis points |
| COR-23 | Hedge coverage and effectiveness | State / intervention | % |
| COR-24 | Inflation rate | Shock | % |
| COR-25 | Interest-rate movement | Shock | Basis points |
| COR-26 | Correspondent-bank availability | Shock | % / count |
| COR-27 | Payment-rail availability | Shock | % |
| COR-28 | Gateway and intermediary availability | Shock | % |
| COR-29 | Number of routing alternatives | State / intervention | Count |
| COR-30 | Route-switching capacity and delay | Intervention | % / hours |
| COR-31 | Settlement cycle | State / shock | Hours / days |
| COR-32 | Settlement failure rate | Shock | % |
| COR-33 | Cut-off time and holiday-calendar effect | State / shock | Hours / days |
| COR-34 | Cross-border transaction fee | Shock | Currency / % |
| COR-35 | Liquidity requirement by currency and corridor | State / shock | Currency |
| COR-36 | Funds trapped by country or corridor | Shock | Currency / % |
| COR-37 | Legal enforceability of claims | Shock | Score / recovery % |
| COR-38 | Insolvency recovery rate and duration | Behaviour | % / months |
| COR-39 | Regulatory divergence between route endpoints | Shock | Index |
| COR-40 | AML, KYC and sanctions friction | Shock | Delay / rejection % |
| COR-41 | Data-localisation or cross-border-data restriction | Shock | Index / binary |
| COR-42 | Tax, withholding and permanent-establishment exposure | Shock | % / currency |
| COR-43 | Port, transport or trade-infrastructure disruption | Shock | % / duration |
| COR-44 | Telecommunications and power reliability | Shock | % |
| COR-45 | Natural-hazard and physical-climate disruption | Shock | Severity / duration |
| COR-46 | Water, heat, flood, storm or wildfire exposure | Shock | Hazard index |
| COR-47 | Supply-chain dependency through the corridor | State | % / criticality score |
| COR-48 | Diplomatic-relations deterioration | Shock | Index |
| COR-49 | Country risk premium | Shock | Basis points |
| COR-50 | Emergency corridor suspension | Intervention | Binary / duration |
| COR-51 | Transaction rerouting allocation | Intervention | % by alternate route |
| COR-52 | Local reserve pre-positioning | Intervention | Currency |

## 8. Derived outcomes — not manipulated directly

The following values are computed from the manipulated variables and should not appear as independent operator controls:

- Enterprise Resilience Index and confidence band;
- capital adequacy and capital-buffer consumption;
- liquidity coverage and liquidity survival horizon;
- expected and unexpected loss;
- probability and severity of enterprise failure;
- held, delayed, failed and reconciled obligations;
- operational continuity and capacity remaining;
- merchant, country and corridor risk classifications;
- regulatory exposure and expected remediation cost;
- systemic propagation velocity and concentration;
- recovery time, recovery probability and recovery trajectory;
- capital-regeneration time and restored-capital level;
- board escalation level and recommended decision.

## 9. Console behaviour

Each master control displays a composite setting calculated from its detailed variables. Selecting a control opens its parameter panel. Changes remain a scenario draft until the operator runs or commits the simulation. The interface shows the proposed delta, affected entities, evidence source, confidence, and downstream outcomes before the scenario is executed.

Dependencies are explicit. A geopolitical shock entered under Countries & Corridors can change regulation, operations, merchant behaviour, liquidity and capital, but those secondary effects are calculated through the dependency model rather than entered repeatedly.
