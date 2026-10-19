# Sri Lanka Public Data Evidence & Contextual Integration Report

**Project:** NeighborNet AI  
**Competition:** ModelX 2.0  
**Phase:** 4.6 — Data Evidence Architecture & Advanced Evaluation  
**Target Pilot Region:** Moratuwa, Ratmalana, Dehiwala, and Colombo South, Western Province, Sri Lanka

---

## 1. Overview & Objective

NeighborNet AI establishes a transparent, reproducible, and verifiable public data evidence foundation. To avoid creating unsupported claims or fabricating partner permissions, NeighborNet AI strictly distinguishes between:
1. **Real Public Observations & Geospatial Context:** Ingested from verified open-access APIs and government/UN publications.
2. **Synthetic Operational Fixtures:** Deterministic test data used for optimization algorithm evaluation.

---

## 2. Public Data Sources & Provenance Register

### Source 1: OpenStreetMap (OSM) Road Network & Food Venues
- **Official Source URL:** [https://download.geofabrik.de/asia/sri-lanka.html](https://download.geofabrik.de/asia/sri-lanka.html) / Overpass API
- **License:** Open Database License (ODbL) 1.0
- **Retrieved Date:** October 11, 2026
- **Geographic Coverage:** Moratuwa Pilot Bounding Box (Lat: 6.75°N to 6.85°N, Lon: 79.85°E to 79.90°E)
- **Coordinate Reference System:** EPSG:4326 (WGS84 lat/lon)
- **Feature Counts:** 1,528 total nodes and ways; 38 verified restaurant & bakery POIs
- **SHA-256 Checksum:** `d52c4859c9e05f63d04fa85c2c54cf9135062a4fa9bfd791522fdfa3e42ea2d6`
- **Application in NeighborNet AI:** Used to extract real road network geometry, calculate realistic courier travel distances, and position pilot donor locations.

### Source 2: Open-Meteo Historical Weather Observations
- **Official Source URL:** [https://open-meteo.com/en/docs/historical-weather-api](https://open-meteo.com/en/docs/historical-weather-api)
- **License:** Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Retrieved Date:** October 11, 2026
- **Geographic Coverage:** Moratuwa / Colombo South (6.7731°N, 79.8816°E)
- **Time Horizon:** September 1, 2026 to September 30, 2026
- **Record Count:** 30 daily reanalysis records
- **Variables Retained:** Daily total rainfall (`rain_sum` in mm), total precipitation (`precipitation_sum` in mm), and daily max/min 2m air temperature (`temperature_2m_max`, `temperature_2m_min` in °C)
- **Missing Value Count:** 0 missing values
- **SHA-256 Checksum:** `8a1e2e7a24a51e600efcddbbdf6bd8dd983f47e06ffefbbd7b2e88a05c3080ff`
- **Application in NeighborNet AI:** Ingested into disaster context modules to provide historical monsoon weather baselines for simulated flood response scenarios.

### Source 3: Sri Lanka Disaster Management Centre (DMC) Situation Reports
- **Official Source URL:** [https://www.dmc.gov.lk/](https://www.dmc.gov.lk/)
- **License:** Public Domain / Government Document
- **Retrieved Date:** October 11, 2026
- **Geographic Coverage:** Western Province (Colombo & Kalutara Districts, including Moratuwa)
- **Extracted Sitreps:** `DMC-SITREP-2026-05-MONSOON` (May 2026 Southwest Monsoon Floods) and `DMC-SITREP-2025-11-CYCLONE` (November 2025 Cyclonic Storm Operations)
- **SHA-256 Checksum:** `7388c9928054c2a7fd06dd2fb67243c1eeeb8ee99b7eb50dc3ae4602f3c21c3b`
- **Application in NeighborNet AI:** Grounding disaster response priorities, shelter capacity parameters, and emergency resource demand patterns in official Sri Lankan disaster sitrep formats.

### Source 4: UNEP Food Waste Index Report 2024
- **Official Report URL:** [https://www.unep.org/resources/global-food-waste-index-report-2024](https://www.unep.org/resources/global-food-waste-index-report-2024)
- **License:** UN Environment Programme Public Document
- **Publication Date:** 2024
- **Scope:** Sri Lanka National Household & Commercial Estimates
- **Key Statistics:** 76 kg/capita/year household food waste estimate; ~1.61 Million Tonnes national annual household food waste
- **SHA-256 Checksum:** `e0b63b97de5d8868997ef31e4e5904be9f52f36d3cb853e34b19ebc578028fef`
- **Application in NeighborNet AI:** Provides macro-level problem validation for Sri Lanka's food rescue potential without extrapolating national totals into false local donor pledges.

---

## 3. Data Integrity & Provenance Boundary Table

| Data Dimension | Source Type | Data Classification | License | Verification Status |
| :--- | :--- | :--- | :--- | :--- |
| Road Geometry & Map POIs | OpenStreetMap | Real Public Geospatial Context | ODbL 1.0 | **VERIFIED API EXTRACT** |
| Daily Rainfall & Temp | Open-Meteo | Real Public Observations | CC BY 4.0 | **VERIFIED API EXTRACT** |
| Disaster Hazard Bounds | SL DMC Reports | Real Public Govt Document | Public Domain | **VERIFIED ARCHIVE EXTRACT** |
| Per-Capita Food Waste | UNEP Report 2024 | Real Public Research Est. | UN Public | **VERIFIED REPORT EXTRACT** |
| Donor Surplus Lots | Synthetic Generator | Synthetic Fixture V1 | Internal | **SYNTHETIC BENCHMARK** |
| NGO Recipient Requests | Synthetic Generator | Synthetic Fixture V1 | Internal | **SYNTHETIC BENCHMARK** |
| Courier Rosters & Vehicles | Synthetic Generator | Synthetic Fixture V1 | Internal | **SYNTHETIC BENCHMARK** |

---

## 4. Limitation & Warning Standard

NeighborNet AI strictly adheres to the following transparency protocol:
- Real spatial and weather data enrich the background context of solver runs.
- Benchmark results measure algorithm performance on deterministic synthetic scenarios (`MODELX_EVAL_ADVANCED_V1`).
- No synthetic transaction or simulated allocation is ever represented as a real Sri Lankan delivery event.
