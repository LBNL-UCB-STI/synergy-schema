# UrbanSim contracts

This directory maintains schemas for both UrbanSim execution modes used across
Synergy and PILATES:

- **Containerized UrbanSim (PILATES / Deliverable #1)**:
  - `urbansim_population.yaml`: `UrbanSimHouseholdPopulationRecord` and
    `UrbanSimPersonPopulationRecord` identity/join fields used by the current
    PILATES population handoff (`enforcement_status: PILATES-observed`). The
    work and school zone aliases are scoped to the current PILATES ActivitySim
    adapter and do not establish a durable cross-model vocabulary.
  - `urbansim_land_use.yaml`: Notional Deliverable #1 land-use and spatial
    crosswalk classes (`UrbanSimBlockMarginals`, `BlockToTazMapping`,
    `UrbanSimZonalTotals`) reflecting the containerized model framing.
- **Cloud API UrbanSim (FY27 primary)**:
  - `urbansim_cloud_v1.yaml`: Observed GCS-backed Parquet I/O contracts for the
    UrbanSim Cloud API service (`UrbanSimCloudSkimsInput` for
    `input_skims.parquet` and `UrbanSimCloudBlockMarginals` for
    `marginals_<year>.parquet`, `enforcement_status: observed_sample`).
    UrbanSim's internal synthesis files (`households_<year>.parquet`,
    `persons_<year>.parquet`, `jobs_<year>.parquet`) are non-authoritative for
    Synergy and are omitted.
