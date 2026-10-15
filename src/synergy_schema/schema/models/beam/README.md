# BEAM Model Contracts

This directory contains LinkML schema contracts for the **BEAM** (Behavior, Energy, Autonomy, and Mobility) dynamic travel simulation engine, observed from the reference implementation in PILATES (`pilates/database/schema/beam_schema.py` and `pilates/beam/postprocessor.py`).

BEAM is an agent-based discrete-event transportation system simulation framework developed at Lawrence Berkeley National Laboratory (LBNL). In the integrated PILATES and Synergy workflows, BEAM consumes synthetic population inputs, executes activity-travel plans, and outputs transportation network travel skims.

## Schema Files

### 1. `beam_population.yaml`
Defines the core agent population inputs consumed by BEAM:
- **`BeamHouseholdRecord`** (aliases: `HouseholdsBeamIn`, `BeamHouseholdInputRecord`): Household attributes including location (`block_id`, `home_zone_id`), income, vehicle availability (`cars`), worker and demographic counts, and value of time.
- **`BeamPersonRecord`** (aliases: `PersonsBeamIn`, `BeamPersonInputRecord`): Person attributes including demographics (`age`, `sex`), employment and student status (`ptype`, `pemploy`, `pstudent`), home and work coordinates/TAZs (`home_x`, `home_y`, `workplace_zone_id`), commute distances, and mobility options (`has_electric_bike`, `has_rideshare`, `has_carshare`).
- **`BeamVehicleRecord`** (aliases: `VehiclesBeamIn`, `BeamVehicleInputRecord`): Household vehicle fleet staged from ATLAS (`vehicles2`), containing vehicle identification, primary driver link (`maindriver_id`), powertrain adoption (`pred_power`), and vehicle type (`vehicleTypeId`).

### 2. `beam_plans.yaml`
Defines the activity-travel itinerary elements:
- **`BeamPlanRecord`** (aliases: `PlansBeamIn`, `BeamPlanInputRecord`): Scheduled daily travel plans provided as input to BEAM, where each element is an activity (purpose, location coordinates, start/end time) or a trip leg (mode, departure time, route links, expected travel time/cost).
- **`BeamPlanOutputRecord`** (aliases: `BeamPlansOut`, `BeamExecutedPlanRecord`): Executed travel plans emitted by BEAM after dynamic simulation and scoring, capturing simulated travel times, actual departure times, and traversed network links.

### 3. `beam_skims.yaml`
Defines network travel impedance outputs produced by BEAM:
- **`BeamNetworkSkims`** (aliases: `BeamSkims`, `BeamSkimsOutput`): **Default and authoritative** multi-modal, multi-period zone-to-zone (TAZ x TAZ) matrix container packaged in Open Matrix (`.omx`) or `Zarr` (`.zarr`) array format (`default_skim_representation: true`). Uses LinkML `array` dimensions (`[origin_zone, destination_zone]` 2D matrices for highway and active modes `DISTWALK`/`DISTBIKE`, and `[time_period, origin_zone, destination_zone]` 3D tensors for multi-period transit IVT/wait times/fares and ridehail/TNC metrics across `EA`, `AM`, `MD`, `PM`, `EV`).
- **`BeamODSkimsRecord`** (aliases: `BeamActivitySimODSkimsRecord`): Secondary intermediate tabular router origin-destination CSV record shape emitted by BEAM (`skimsActivitySimOD_current.csv.gz`) prior to OMX/Zarr matrix aggregation (`default_skim_representation: false`).

### 4. `beam.yaml`
Consolidated schema package that imports `beam_population`, `beam_plans`, and `beam_skims`.
