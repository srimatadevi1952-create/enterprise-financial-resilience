# Strategic Corridor Matrix

This inventory covers 15 jurisdictions and 210 directed corridors. The reverse direction is listed separately because settlement, FX, compliance, and cut-off behavior can differ by direction.

## Jurisdictions

| Code | Jurisdiction | Currency | Initial priority |
|---|---|---|---|
| IN | India | INR | High |
| GB | United Kingdom | GBP | High |
| SG | Singapore | SGD | High |
| US | United States | USD | High |
| AE | United Arab Emirates | AED | High |
| SA | Saudi Arabia | SAR | High |
| DE | Germany / Eurozone | EUR | High |
| NL | Netherlands / Eurozone | EUR | Medium |
| CH | Switzerland | CHF | Medium |
| JP | Japan | JPY | Medium |
| HK | Hong Kong | HKD | Medium |
| AU | Australia | AUD | Medium |
| CA | Canada | CAD | Medium |
| BR | Brazil | BRL | Medium |
| ZA | South Africa | ZAR | Medium |

## Corridor scope

- Directed corridors: **210**
- Undirected country pairs: **{len(rows)//2}**
- Standard dimensions: FX, cut-off timing, compliance, settlement, liquidity

The CSV contains the complete directed matrix. M18 should activate corridors in priority order rather than treating every corridor as equally exposed.