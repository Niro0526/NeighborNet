# NeighborNet AI — Data Source Register

**Version:** 1.0 (Phase 4.6 Final)  
**Maintained By:** NeighborNet AI Engineering Team  
**Repository Directory:** `data/`

---

## 1. Directory Structure

```text
data/
├── external/
│   ├── osm/
│   │   ├── osm_moratuwa_pilot.json
│   │   └── metadata.json
│   ├── weather/
│   │   ├── open_meteo_moratuwa_sep2026.json
│   │   └── metadata.json
│   └── disaster/
│       ├── dmc_situation_reports.json
│       └── metadata.json
├── processed/
│   └── README.md
├── synthetic/
│   └── README.md
├── evidence/
│   ├── unep_food_waste_sri_lanka.json
│   └── metadata.json
└── scripts/
    └── ingest_sri_lanka_data.py
```

---

## 2. Ingested Dataset Register

### Item 1: OpenStreetMap Moratuwa Extract
- **File Path:** `data/external/osm/osm_moratuwa_pilot.json`
- **Manifest Path:** `data/external/osm/metadata.json`
- **Source URL:** `https://overpass-api.de/api/interpreter`
- **Retrieved Date:** `2026-10-11T00:54:12Z`
- **Dataset Classification:** `PUBLIC_GEOSPATIAL_CONTEXT`
- **License:** Open Database License (ODbL) 1.0
- **Feature Count:** 1,528 features (38 food venue POIs)
- **CRS:** `EPSG:4326`
- **SHA-256:** `d52c4859c9e05f63d04fa85c2c54cf9135062a4fa9bfd791522fdfa3e42ea2d6`

### Item 2: Open-Meteo Weather Reanalysis
- **File Path:** `data/external/weather/open_meteo_moratuwa_sep2026.json`
- **Manifest Path:** `data/external/weather/metadata.json`
- **Source URL:** `https://archive-api.open-meteo.com/v1/archive`
- **Retrieved Date:** `2026-10-11T00:54:13Z`
- **Dataset Classification:** `PUBLIC_REAL_OBSERVATIONS`
- **License:** Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Record Count:** 30 daily records (Sept 1–30, 2026)
- **SHA-256:** `8a1e2e7a24a51e600efcddbbdf6bd8dd983f47e06ffefbbd7b2e88a05c3080ff`

### Item 3: Disaster Management Centre Sitreps
- **File Path:** `data/external/disaster/dmc_situation_reports.json`
- **Manifest Path:** `data/external/disaster/metadata.json`
- **Source URL:** `https://www.dmc.gov.lk/`
- **Retrieved Date:** `2026-10-11T00:54:14Z`
- **Dataset Classification:** `PUBLIC_GOVERNMENT_DOCUMENTS`
- **License:** Public Domain
- **Record Count:** 2 extracted sitreps (`DMC-SITREP-2026-05-MONSOON`, `DMC-SITREP-2025-11-CYCLONE`)
- **SHA-256:** `7388c9928054c2a7fd06dd2fb67243c1eeeb8ee99b7eb50dc3ae4602f3c21c3b`

### Item 4: UNEP Food Waste Index 2024
- **File Path:** `data/evidence/unep_food_waste_sri_lanka.json`
- **Manifest Path:** `data/evidence/metadata.json`
- **Source URL:** `https://www.unep.org/resources/global-food-waste-index-report-2024`
- **Retrieved Date:** `2026-10-11T00:54:14Z`
- **Dataset Classification:** `PUBLIC_RESEARCH_ESTIMATES`
- **License:** UN Public Document
- **Record Count:** 1 national baseline summary
- **SHA-256:** `e0b63b97de5d8868997ef31e4e5904be9f52f36d3cb853e34b19ebc578028fef`

---

## 3. Ingestion Reproducibility Command

To re-run data ingestion and re-verify checksums:

```bash
python data/scripts/ingest_sri_lanka_data.py
```
