# Field Mappings & Table Handoffs

This reference specifies the single-year table handoffs, module entry points, join keys, categorical crosswalks (`X-H1` to `X-V5`), probabilistic donor draws (`D-H1` to `D-V2`), and unmapped residue fields across **UrbanSim**, **DEMOS**, **ATLAS**, **POLARIS**, **ActivitySim**, **BEAM**, **SynthFirm**, and **Network Skims** (`.omx` / `.zarr`).

The **DEMOS / ATLAS → POLARIS** mappings implement the multi-team specification in `docs/resources/DEMOS_and_ATLAS_to_POLARIS_interface.xlsx` (Section 5), validated on the Austin regional pilot datasets. Counterpart module entry points for **ActivitySim**, **BEAM**, **SynthFirm**, and post-run state feedback appear alongside them so model teams at ANL, NLR, and LBNL can verify interface compatibility across both serial and parallel workflows.

> **Visual Diagrams**: See [Database ER Diagrams](interactive-schema.md) for crow's-foot relational schemas and [Architecture & UML](deliverable_1_uml.md) for workflow pipelines and class diagrams.
>
> **From Static Contract to Multi-Year Execution**: These boundary rules map into three execution tiers for multi-year simulation workflows:
>
> 1. **Relational SQL Projections (`direct`, `renamed`, `aggregated`, `wide_to_long`, and `X-H1` to `X-V5` crosswalks)**: SQL queries execute deterministic table joins, `CASE WHEN` and lookup-table recodes, within-household `ROW_NUMBER()` indexing, and wide-to-long fleet unpivots over boundary tables.
> 2. **Probabilistic Donor Imputation & Longitudinal Progression (`D-H1` to `D-V2` donor draws & `X-P4` to `X-P5`)**: Hash-seeded Python operators impute missing attributes from stratified ACS PUMS and NHTS donor pools to maintain data compatibility across models, while carrying forward time-invariant demographics and locations across simulation years.
> 3. **Runtime Travel-Model Assignment (`work_location_id`, `school_location_id`, `journey_to_work_*`, `ecom`, `num_groceries`, `num_meals`)**: Handoff projections initialize these columns with schema-valid defaults so POLARIS or ActivitySim and BEAM can populate them during simulation.

---

## 1. Table-to-Table Exchange Summary Matrix

| Source Model & Artifact | Target Model & Artifact | Exchange Type | Join / Reference Key | Core Attributes Transferred |
| :--- | :--- | :--- | :--- | :--- |
| [`InputNetworkSkims`](../schema/InputNetworkSkims.md) (.omx) | **UrbanSim** (`input_skims`) | Matrix Skims (1D/2D `array`) | `[origin_zone, destination_zone]` / `[origin_zone]` | `sov_time_am`, `sov_distance`, `transit_accessibility_index` |
| [`UrbanSimZonalTotals`](../schema/UrbanSimZonalTotals.md) | **POLARIS** `Supply.sqlite/Zone` | Zonal Aggregation | `zone_id` ↔ `zone` | `residential_area`, `commercial_area`, `pop_households`, `employment_*` |
| [`UrbanSimBlockMarginals`](../schema/UrbanSimBlockMarginals.md) | **DEMOS** (`marginal_targets`) | Control Totals (`M_t+1`) | `block_id` | `total_households`, `total_population`, `total_workers`, `jobs_total` |
| `DEMOS` Household ([`DemosPolarisMappedHousehold`](../schema/DemosPolarisMappedHousehold.md)) | **POLARIS** `Demand.sqlite/Household` ([`PolarisDemandDatabaseHousehold`](../schema/PolarisDemandDatabaseHousehold.md)) | Tabular Microdata | `household` | `income`, `workers`, `persons`, `age_of_head`, `race_of_head`, `type`, `location` |
| `DEMOS` Person ([`DemosPolarisMappedPerson`](../schema/DemosPolarisMappedPerson.md)) | **POLARIS** `Demand.sqlite/Person` ([`PolarisDemandDatabasePerson`](../schema/PolarisDemandDatabasePerson.md)) | Tabular Microdata | `(household, id)` | `age`, `gender`, `relp`, `education`, `employment`, `school_enrollment` |
| `DEMOS` Household ([`DemosPolarisMappedHousehold`](../schema/DemosPolarisMappedHousehold.md)) | **ATLAS** `atlas_hh` | Tabular Microdata | `household` ↔ `HOUSEID` | Household identity, composition, and income |
| `ATLAS` Vehicle ([`AtlasVehicleFleetOutput`](../schema/AtlasVehicleFleetOutput.md)) | **POLARIS** `Demand.sqlite/Vehicle` ([`PolarisDemandDatabaseVehicle`](../schema/PolarisDemandDatabaseVehicle.md)) | Tabular Microdata | `(HOUSEID, VEHID)` ↔ `(household, id)` | `bodytype`, `pred_power`, `modelyear`, `annual_mileage` |
| **POLARIS** DTA Solver | [`NextYearNetworkSkims`](../schema/NextYearNetworkSkims.md) (.omx) | Matrix Skims (2D `array`) | `[origin_zone, destination_zone]` | `sov_time_am`, `sov_time_pm`, `congestion_index` |
| **POLARIS** Post-Run State ([`PolarisHouseholdStateOutput`](../schema/PolarisHouseholdStateOutput.md), [`PolarisPersonStateOutput`](../schema/PolarisPersonStateOutput.md)) | **Year t+1 Core Population** (`Demand.sqlite` / `Result.sqlite`, provisional) | Longitudinal State Feedback | `household`, `person` | `location`, `time_in_home`, `ecom`, `work_location_id`, `school_location_id`, `journey_to_work_*`, `telecommute_level`, `transit_pass`, `escooter_use_level`, `time_in_job`, `is_long_term_chooser` (A20, A21, A23, A30, A31) |
| **BEAM** Dynamic Simulation | [`BeamNetworkSkims`](../schema/BeamNetworkSkims.md) & [`ActivitySimNetworkSkims`](../schema/ActivitySimNetworkSkims.md) (.omx / .zarr, default) | Matrix Skims (1D/2D/3D `array`) | `[time_period, origin_zone, destination_zone]` / `/lookup` `[origin_zone]` | Required core (provisional): `DIST`, `DISTWALK`, `SOV_{TIME,DIST,BTOLL}`, `WLK_TRN_WLK_{IVT,IWAIT,XWAIT,WACC,WAUX,WEGR}`; Optional (provisional): `DISTBIKE`, `SOVTOLL_*`, `HOV2*`, `HOV3*`, submode transit `WLK_{LOC,LRF,EXP,HVY,COM}_*` / `DRV_*`, `ridehail_*` |
| [`UrbanSimBlockMarginals`](../schema/UrbanSimBlockMarginals.md) | **SynthFirm** [`SynthFirmEstablishmentRecord`](../schema/SynthFirmEstablishmentRecord.md) | Zonal Control | `block_id` ↔ `MESOZONE` | Zonal employment by NAICS industry, commercial/industrial floor space |
| **SynthFirm** Establishments | **SynthFirm** [`SynthFirmB2BShipmentRecord`](../schema/SynthFirmB2BShipmentRecord.md) | Freight Contracts | `BusID` ↔ `SellerID`/`BuyerID` | Commodity SCTG 1 to 5, shipment tonnage, truckload, private/for-hire carrier |
| **SynthFirm** Fleets ([`SynthFirmEstablishmentRecord`](../schema/SynthFirmEstablishmentRecord.md)) | **POLARIS** `Demand.sqlite/Vehicle` ([`PolarisDemandDatabaseVehicle`](../schema/PolarisDemandDatabaseVehicle.md)) | Commercial Fleets (`wide_to_long`) | `BusID` ↔ `hhold` / `fleet_id` ↔ `fleet` | Wide fleet counts (`diesel_class_1_2a`..`electric_class_7_8_vocational`, `EV_powertrain`) unpivoted to discrete vehicles (`vehicle_id`, `fleet`, `type` via `Vehicle_Type`) |
| **SynthFirm** Shipments | **BEAM** `freight-plans.xml` ([`BeamPlanRecord`](../schema/BeamPlanRecord.md)) | Freight Tours | `BusID` ↔ `depot_id` | Commercial multi-stop tours, payload, and depot charging profiles |

> **Provisional Boundaries Flagged for Collaborator Verification**
>
> - **OMX / Zarr Skim Mode Split (`BeamNetworkSkims` & `ActivitySimNetworkSkims`)**: Based on the production MTC / ActivitySim / BEAM `skims.omx` contract (`OMX_VERSION = '0.2'`, `SHAPE = [N_zones, N_zones]`), the schema requires static distances (`DIST`, `DISTWALK`), free-lane SOV auto (`SOV_TIME`, `SOV_DIST`, `SOV_BTOLL`), and walk-transit-walk accessibility skims (`WLK_TRN_WLK_{IVT,IWAIT,XWAIT,WACC,WAUX,WEGR}`), while setting `required: false` (`status: provisional`) on managed-lane (`SOVTOLL_*`, `HOV2*`, `HOV3*`), bike (`DISTBIKE`), transit submode (`WLK_{LOC,LRF,EXP,HVY,COM}_*`, `DRV_*`), and ridehail (`RH_*`) arrays.
> - **POLARIS Post-Run State Feedback (`PolarisHouseholdStateOutput` & `PolarisPersonStateOutput`)**: Captures the post-simulation household and person state attributes feeding Year `t+1` (`A20`, `A21`, `A23`, `A30`, `A31`); exact SQLite output table and column names carry `status: provisional` pending ANL confirmation.
> - **SynthFirm Commercial Fleet Unpivot**: `SynthFirmEstablishmentRecord` stores truck fleets in 13 wide fuel-by-FHWA-class columns; mapping into `PolarisDemandDatabaseVehicle` applies a `wide_to_long` expansion and links establishment `BusID` to `Vehicle.hhold`.

---

## 2. Column-Level Mapping Specifications & Residue

=== "DEMOS Household → POLARIS"

    | DEMOS Column | POLARIS Column | Mode | Rule / Crosswalk | Description & Residue Handling |
    | :--- | :--- | :--- | :--- | :--- |
    | `household` | `household` | `direct` | Identity | Integer household primary key (identifies surviving vs. new households). |
    | `income` | `income` | `derived` | Deflated & Rounded | Deflated to base-year USD and rounded to nearest integer dollar. |
    | `persons` | `size` | `renamed` | Count | Total count of individuals in household. |
    | `workers` | `workers` | `derived` | **X-P2** | Count of persons with ESR 1 or 4 (employed and at work). |
    | `age_of_head` | `age_of_head` | `direct` | Pass-through | Age of reference person (`relp = 0`). |
    | `race_of_head`| `race` | `enum_crosswalk`| **X-P1** / **D-P3b** | Census PUMS race code to POLARIS race (1 to 9). |
    | `lcm_county_id`| `county` | `direct` | Pass-through | 5-digit State/County FIPS (e.g. 48453). |
    | `block_id` | `location` | `derived` | **D-H1** | 11-digit Census tract GEOID (`popsyn_region`). New households draw dwelling location via **D-H1**. Surviving households retain location. |
    | *(Composition)*| `type` | `derived` | **X-H1**, **X-H2** | Recomputed from composition: HHT × tenure → POLARIS `HHTYPE` (1..11). |
    | *(D-H1)* | `housing_unit_type`| `derived` | **X-H3** / **D-H1** | Carried for surviving households; drawn with dwelling for new households. |
    | *(D-H1)* | `Has_Residential_Charging`| `derived` | **D-H1** | Drawn together with dwelling; preserved for surviving households. |
    | `SERIALNO_PUMS`| None | *Residue* | Lineage Trace | Census PUMS seed record identifier; retained for auditability, not stored in POLARIS. |
    | `is_reorg_household`| None | *Residue* | Internal State | DEMOS demographic restructuring flag; unmapped in POLARIS. |
    | *(Aggregated)* | `vehicles` | `aggregated`| **X-V1..X-V5** | Count of associated vehicle records from ATLAS fleet output (or **D-H2** interim). |

=== "DEMOS Person → POLARIS"

    | DEMOS Column | POLARIS Column | Mode | Rule / Crosswalk | Description & Residue Handling |
    | :--- | :--- | :--- | :--- | :--- |
    | `household` | `household` | `direct` | Foreign Key | Foreign key to Household table. |
    | `id` | `id` | `derived` | 0..n-1 Ordinal | Regenerated within-household ordinal index (0, 1, ..., n-1). |
    | `person` | None | *Residue* | Lineage Trace | Global synthetic person identifier; preserved in DEMOS outputs. |
    | `age` | `age` | `direct` | Pass-through | Person chronological age in years. |
    | `gender` | `gender` | `direct` | **X-P1** | 1 = Male, 2 = Female. |
    | `relp` | `relp` | `direct` | **X-P1** | PUMS relationship code (0..15) mapped to POLARIS RELP (0..17). |
    | `education` | `education` | `direct` | **X-P1**, **X-P6** | 0..24 ACS SCHL code; K-12 consistency enforced via **X-P6**. |
    | `employment` | `employment` | `direct` | **X-P1**, **X-P2** | ACS ESR code (0..6). Workers are ESR 1 and 4. |
    | `school_enrollment`| `school_enrollment`| `direct`| **X-P1** | 0 NA, 1 none, 2 public, 3 private. Public/private continuity maintained. |
    | `marital_status`| `marital_status`| `direct` | **X-P1** / **D-P3a** | 1 Married, 2 Widowed, 3 Divorced, 4 Separated, 5 Never married. 0 resolved via **D-P3a**. |
    | `income` | `income` | `derived` | Deflated | Individual personal earned income (deflated to base year). |
    | *(Derived)* | `school_grade_level`| `derived` | **X-P3..X-P5** | Continuing students advance via **X-P4**; entrants draw via **X-P5**. |
    | *(D-P1)* | `worker_class`, `industry`, `work_hours` | `derived` | **D-P1**, **X-P7** | Donor draw conditioned on county × sex × age group × education group. |
    | *(D-P2)* | Commute attributes | `derived` | **D-P2** | Mode, travel time, occupancy, arrival time drawn for at-work persons. |
    | `SERIALNO_PUMS`| None | *Residue* | Lineage Trace | Census PUMS household seed identifier. |
    | `SPORDER` | None | *Residue* | Lineage Trace | Census PUMS person seed sequence ordinal. |

=== "ATLAS Vehicle → POLARIS"

    | ATLAS Column | POLARIS Column | Mode | Rule / Crosswalk | Description & Residue Handling |
    | :--- | :--- | :--- | :--- | :--- |
    | `HOUSEID` | `hhold` | `renamed` | Foreign Key | Owning household ID. Must exist in POLARIS population. |
    | `VEHID` | `vehicle_id` | `derived` | Sequence | Retained vehicles keep previous ID; new vehicles take next available ID. |
    | `bodytype` | `vehicle_class` | `derived` | **X-V1**, **D-V1** | Retained keep size; new vehicles draw size class within body type via **D-V1**. |
    | `pred_power` | `powertrain_type`| `enum_crosswalk`| **X-V2** | ICE → Conventional (0), Hybrid → HEV (1), PHEV → PHEV (2), AEV → BEV_long (3). |
    | *(Derived)* | `fuel_type` | `derived` | **X-V3**, **D-V2** | BEV → Elec (4); HEV/PHEV → Gas (0); Conventional draws Gas (0) or Diesel (1) via **D-V2**. |
    | `modelyear` | `vintage_type` | `derived` | **X-V4** | Recomputed each year from age = SimulationYear - modelyear (0 = 0 to 5y, 1 = 6 to 10y, 2 = 10+y). |
    | *(Composite)* | `type` | `derived` | **X-V5** | Looked up in POLARIS `Vehicle_Type` on `(class, connectivity, powertrain, automation, fuel, vintage)`. |
    | `annual_mileage`| None | *Residue* | Behavioral Model | Estimated annual VMT; used for activity allocation. |
    | `vintage_category`| None | *Residue* | Validation | Categorical vintage cross-checked against `modelyear`. |

=== "UrbanSim Zonal Totals → POLARIS Supply"

    | UrbanSim Column | POLARIS Column | Mode | Description |
    | :--- | :--- | :--- | :--- |
    | `zone_id` | `zone` | `direct` | Traffic Analysis Zone (TAZ) integer primary key. |
    | `residential_area` | `residential_area` | `direct` | Total residential floor/lot area. |
    | `commercial_area` | `commercial_area` | `direct` | Total commercial development area. |
    | `office_area` | `office_area` | `direct` | Total office floor area. |
    | `retail_area` | `retail_area` | `direct` | Total retail shopping area. |
    | `industrial_area` | `industrial_area` | `direct` | Industrial/warehouse space. |
    | `institutional_area`| `institutional_area`| `direct`| Civic, institutional, and medical land area. |
    | `pop_households` | `pop_households` | `direct` | Marginal control total of households residing in zone. |
    | `pop_persons` | `pop_persons` | `direct` | Marginal control total of persons residing in zone. |
    | `employment_total` | `employment_total` | `direct` | Total employment count located in zone. |
    | `employment_retail`| `employment_retail`| `direct` | Retail sector employment. |
    | `employment_services`| `employment_services`| `direct`| Service sector employment. |
    | `employment_government`| `employment_government`| `direct`| Public administration & government employment. |
    | `employment_manufacturing`| `employment_manufacturing`| `direct`| Manufacturing sector employment. |
    | `hh_inc_avg` | `hh_inc_avg` | `direct` | Mean household income within zone. |

=== "UrbanSim → SynthFirm Establishments"

    | UrbanSim Column | SynthFirm Column | Mode | Description & Allocation Handling |
    | :--- | :--- | :--- | :--- |
    | `block_id` | `MESOZONE` | `direct` | 11-digit Census Block Group FIPS identifier anchoring the establishment. |
    | `county_id` | `CBPZONE` | `derived` | County identifier used for CBP marginal employment scaling. |
    | `jobs_total` | `Emp` | `derived` | Establishment synthetic employment scaled to match zonal total employment controls. |
    | `commercial_sqft`| None | *Residue* | Floor space capacity constraint used during spatial firm synthesis. |
    | `jobs_retail` | None | *Residue* | Subsector retail employment control total. |
    | `jobs_service` | None | *Residue* | Subsector service employment control total. |

=== "SynthFirm Fleets → POLARIS Commercial Vehicles"

    `SynthFirmEstablishmentRecord` stores commercial fleets in **wide format** across 13 fuel-by-FHWA-class count columns (`diesel_class_1_2a` .. `electric_class_7_8_vocational`), `EV_powertrain`, and aggregate `n_trucks`. A `wide_to_long` unpivot expands non-zero fleet counts into discrete commercial vehicle records targeting `PolarisDemandDatabaseVehicle` (and `PolarisDemandDatabaseVehicleType`):

    | SynthFirm Column | POLARIS Column | Mode | Rule / Crosswalk | Description & Residue Handling |
    | :--- | :--- | :--- | :--- | :--- |
    | `BusID`, `MESOZONE` | `hhold` *(or depot TAZ)* | `derived` | Depot / Owner Link | Establishment identifier (`BusID`) and zone (`MESOZONE`) anchor the commercial vehicle owner (`Vehicle.hhold`) and depot TAZ location (`PolarisDemandDatabaseVehicle` has no `location` column). |
    | `fleet_id` *(unpivoted index)* | `vehicle_id`, `fleet` | `wide_to_long` | Sequence | Sub-fleet allocation index (`fleet_id`) expanded across `n_trucks` to assign unique `Vehicle.vehicle_id` and commercial `Vehicle.fleet` indicator. |
    | `diesel_class_1_2a` .. `electric_class_7_8_vocational` | `Vehicle_Type.vehicle_class`, `Vehicle_Type.fuel_type`, `Vehicle.type` | `wide_to_long` | **X-V1**, **X-V3**, **X-V5** | 13 wide fuel × class count columns unpivoted into discrete vehicle rows; FHWA class and fuel resolve to composite `Vehicle_Type.type_id` (`Vehicle.type`). |
    | `EV_powertrain` | `Vehicle_Type.powertrain_type` | `enum_crosswalk` | **X-V2**, **X-V5** | Maps `SynthFirmPowertrainEnum` (`BEV`, `PHEV`, `FCEV`) to `Vehicle_Type.powertrain_type` (and `fuel_type` = Electricity/H2) when resolving `Vehicle.type`. |
    | `n_trucks` | None | *Residue* | Unpivot Total Check | Aggregate establishment truck count; equals the sum of unpivoted commercial vehicle rows generated for `(BusID, fleet_id)`. |

=== "SynthFirm B2B Shipments → BEAM Freight Plans"

    | SynthFirm Column | BEAM Column | Mode | Rule / Crosswalk | Description & Residue Handling |
    | :--- | :--- | :--- | :--- | :--- |
    | `shipment_id` | `payload_id` | `direct` | Identity | Unique shipment payload identifier. |
    | `SellerID` | `origin_depot` | `derived` | Depot Lookup | Seller business establishment depot location (lat/lon). |
    | `BuyerID` | `destination` | `derived` | Facility Lookup | Buyer business establishment receiving location (lat/lon). |
    | `Commodity_SCTG`| `commodity_type`| `direct` | SCTG 1 to 5 | Commodity class (1=Ag/Mining, 2=Mfg, 3=Chemical, 4=Equip, 5=Misc). |
    | `TruckLoad` | `payload_tons` | `direct` | Tons | Weight of shipment in US short tons. |
    | `Mode` | `mode` | `enum_crosswalk`| Mode Choice | Private Truck, For-Hire Truck, or Rail drayage. |

---

## 3. Categorical Crosswalks (`X-H1` – `X-V5`)

=== "Household Crosswalks (X-H1 – X-H3)"

    ### Crosswalk X-H1: Household Type (HHT) from Composition

    Evaluated in strict order using the household's final person composition:

    1. If any member has `relp = 1` (spouse) → **Married-couple family**
    2. Else if any member has `relp = 2..10` (relative) and head `gender = 1` → **Other family, male head**
    3. Else if any member has `relp = 2..10` (relative) and head `gender = 2` → **Other family, female head**
    4. Else if `persons = 1` → **Nonfamily, living alone**
    5. Otherwise → **Nonfamily, not living alone**

    *(Nonrelatives with `relp` 11 to 15 do not constitute a family).*

    ### Crosswalk X-H2: Tenure × HHT → POLARIS Type (`HHTYPE`)

    | HHT | Own (`tenure = 1`) | Rent (`tenure = 2`) |
    | :--- | :--- | :--- |
    | Married-couple family | `1` (`HHT_OWN_FAMILY_MARRIED`) | `6` (`HHT_RENT_FAMILY_MARRIED`) |
    | Other family, male head | `2` (`HHT_OWN_FAMILY_MALE`) | `7` (`HHT_RENT_FAMILY_MALE`) |
    | Other family, female head | `3` (`HHT_OWN_FAMILY_FEMALE`) | `8` (`HHT_RENT_FAMILY_FEMALE`) |
    | Nonfamily, living alone | `4` (`HHT_OWN_NONFAMILY_SINGLE`) | `9` (`HHT_RENT_NONFAMILY_SINGLE`) |
    | Nonfamily, not living alone | `5` (`HHT_OWN_NONFAMILY_OTHER`) | `10` (`HHT_RENT_NONFAMILY_OTHER`) |
    | Group quarters | `11` (`HHT_GQ`) | `11` (`HHT_GQ`) |

    ### Crosswalk X-H3: Housing Unit Type (`HU_TYPE`)

    - `1` → `HU_SINGLE_FAMILY` (Single Family Detached)
    - `2` → `HU_SMALL_APT_BLD` (2 to 9 units)
    - `3` → `HU_LARGE_APT_BLD` (10+ units)
    - `4` → `HU_OTHER` (Mobile home, RV, boat)
    - `5` → `HU_GROUP_QUARTERS` (GQ institutional / non-institutional)

=== "Person Crosswalks (X-P1 – X-P7)"

    ### Crosswalk X-P1: DEMOS Person Variables → POLARIS

    - `relp`: 0 to 15 → 0 to 17 (RELP; 16 and 17 reserved for Group Quarters).
    - `gender`: 1 Male, 2 Female.
    - `age`: Integer → Integer.
    - `education`: 0 to 24 (ACS SCHL code).
    - `employment`: 0 to 6 (ACS ESR code).
    - `school_enrollment`: 0 NA, 1 None, 2 Public, 3 Private.
    - `marital_status`: 1 Married, 2 Widowed, 3 Divorced, 4 Separated, 5 Never married. Code `0` resolved via fallback **D-P3a**.
    - `income`: Deflated and rounded to integer dollars.
    - `id`: Within-household index renumbered `0..n-1`.

    ### Crosswalk X-P2: Employment (ESR) Groups & Worker Identification

    | ESR | Label | Employed? | At Work? | Drives POLARIS Worker? |
    | :--- | :--- | :--- | :--- | :--- |
    | `0` | Under 16 | No | No | No |
    | `1` | Civilian, at work | Yes | Yes | **Yes** (`Household.workers += 1`) |
    | `2` | Civilian, job but not at work | Yes | No | No |
    | `3` | Unemployed | No | No | No |
    | `4` | Armed forces, at work | Yes | Yes | **Yes** (`Household.workers += 1`) |
    | `5` | Armed forces, job but not at work | Yes | No | No |
    | `6` | Not in labor force | No | No | No |

    ### Crosswalk X-P3: School Grade Level & School Type

    - `0` (GRADE_NA) → None
    - `1` (Preschool) → `PREK`
    - `2` (Kindergarten) → `K-8`
    - `3–10` (Grades 1 to 8) → `K-8`
    - `11–14` (Grades 9 to 12) → `9-12`
    - `15` (Undergraduate) → `Higher education`
    - `16` (Graduate) → `Higher education`

    ### Crosswalk X-P4: Grade Progression for Continuing Students

    - Grade `1` (Preschool) → `2` if age ≥ 5, else `1`.
    - Grades `2–13` → Previous grade + 1.
    - Grade `14` (Grade 12) → `15` (Undergraduate).
    - Grade `15` (Undergraduate) → `16` (Graduate) if DEMOS education rose to ≥ 21, else `15`.
    - Grade `16` (Graduate) → `16`.

    ### Crosswalk X-P5: Entry Grade for School Entrants

    - **Ages 3 to 17**: Draw from reference distribution of grades among enrolled persons of same age.
    - **Ages 18+**: Draw conditioned on educational attainment:
      - ≤ 15: Primary weight on Grade 14.
      - 16 to 20: Primary weight on Undergraduate (Grade 15).
      - ≥ 21: Graduate (Grade 16) or Undergraduate (Grade 15).

    ### Crosswalk X-P6: K-12 Education Consistency

    For grade code `g ∈ [1, 14]`:

    - Allowed education: `g` or `g + 1`.
    - If DEMOS education is outside this range: Set `education = g`.

    ### Crosswalk X-P7: Industry Groups & Simple INDP Mapping

    Maps Census ACS INDP codes to POLARIS `EMPLOYMENT_INDUSTRY_SIMPLE`:

    - **INDUSTRIAL**: INDP ≤ 770 or 6070 to 6390.
    - **MANUFACTURING**: INDP 771 to 3990.
    - **RETAIL**: INDP 3991 to 5790.
    - **SERVICE**: INDP 5791 to 7790 (except 6070 to 6390) or 8660 to 9290.
    - **GOVERNMENT**: INDP 7860 to 7890 or 9370 to 9870.
    - **OTHER**: All remaining codes.

=== "Vehicle Crosswalks (X-V1 – X-V5)"

    ### Crosswalk X-V1: ATLAS Body Type → POLARIS Vehicle Class Candidates

    | ATLAS `bodytype` | POLARIS `vehicle_class` Candidates | Base Market Share |
    | :--- | :--- | :--- |
    | `car` | `1` CAR_COMPACT<br/>`2` CAR_MID_SIZE<br/>`3` CAR_FULL_SIZE | 46.9%<br/>43.9%<br/>9.2% |
    | `suv` | `4` SUV_COMPACT<br/>`5` SUV_MID_SIZE<br/>`6` SUV_FULL_SIZE | 36.4%<br/>47.5%<br/>16.2% |
    | `pickup` | `7` PICKUP_MID_SIZE<br/>`8` PICKUP_FULL_SIZE | 19.5%<br/>80.5% |
    | `van` | `6` SUV_FULL_SIZE | 100.0% (Fixed; seats 7, 5.5m long) |

    ### Crosswalk X-V2: ATLAS Predicted Powertrain → Powertrain Type

    | ATLAS `pred_power` | POLARIS `powertrain_type` | Description |
    | :--- | :--- | :--- |
    | `ICE` | `0` (`Conventional`) | Standard internal combustion engine (gasoline/diesel). |
    | `Hybrid` | `1` (`HEV`) | Non-plug-in Hybrid Electric Vehicle. |
    | `PHEV` | `2` (`PHEV`) | Plug-in Hybrid Electric Vehicle. |
    | `AEV` | `3` (`BEV_long`) | All-Electric Battery Electric Vehicle (long range). |

    ### Crosswalk X-V3: Powertrain Type → Fuel Type

    - `Conventional` → Gas (`0`) or Diesel (`1`) via draw **D-V2**.
    - `HEV` → Gas (`0`).
    - `PHEV` → Gas (`0`).
    - `BEV_long` → Electricity (`4`).

    ### Crosswalk X-V4: Vehicle Modelyear → Vintage Type

    Recomputed each year from vehicle age (`age = SimulationYear - modelyear`):

    - age ≤ 5 → `0` (0 to 5 years)
    - 6 ≤ age ≤ 10 → `1` (6 to 10 years)
    - age ≥ 11 → `2` (10+ years)

    ### Crosswalk X-V5: POLARIS `Vehicle_Type` Composite Key Reference

    Every valid vehicle row must resolve to an existing composite key in POLARIS `Vehicle_Type`:
    `(vehicle_class, connectivity_type, powertrain_type, automation_type, fuel_type, vintage_type)`.
    Connectivity is initialized to `0` (No) and automation to `0` (Level 0 / Human driven).

---

## 4. Donor Draws, Staging Pipeline, and Network Skims

=== "Donor Draws Specification Register (D-H1 – D-V2)"

    When POLARIS requires household, person, or vehicle attributes that UrbanSim, DEMOS, or ATLAS do not generate, probabilistic imputation draws those fields from stratified ACS PUMS, NHTS, and base-year reference pools:

    | Draw ID | Target Entity | Donor Attributes Copied | Stratification / Segmentation | Fallback / Collapse Order |
    | :--- | :--- | :--- | :--- | :--- |
    | **D-H1** | New Households | `location`, `tenure`, `housing_unit_type`, `Has_Residential_Charging` | Census tract × head age × size × income | Income → size → head age → tract alone → county |
    | **D-H2** | New Households (Interim) | Complete vehicle fleet rows | Tract × adults × workers × income | Income → workers → adults → county |
    | **D-P1** | Persons ≥ 16 | `worker_class`, `industry`, `work_hours` | County × sex × work age group × education | Education → age → sex → region |
    | **D-P2** | At-work Persons | `journey_to_work_*` (mode, travel time, occupancy, arrival) | Home tract × industry group × full-time flag | Full-time → county × industry → county |
    | **D-P3a**| Persons | `marital_status` (fallback for DEMOS code 0) | Sex × work age × relp group | Regional sex × age pool |
    | **D-P3b**| Persons (`relp > 0`) | `race` (non-head household members) | Head's race × relp group | Head's race alone |
    | **D-P4** | Persons | `disability` status | Sex × disability age group | Disability age group alone |
    | **D-V1** | New Vehicles | `vehicle_class` within ATLAS body type | County × income class × powertrain group | Powertrain → income → county |
    | **D-V2** | Conventional Vehicles| `fuel_type` (Gasoline vs. Diesel) | `vehicle_class` × owner's county | `vehicle_class` regional pool |

=== "13-Step Process Pipeline"

    1. **Step 1 (Inputs & Classification)**: Read DEMOS year t, POLARIS year t-1, and reference population. Classify records into Surviving, New, Removed, and Group Quarters (GQ).
    2. **Step 2 (Direct Person Values)**: Apply deflated income, gender, age, relp, employment, and marital status.
    3. **Step 3 (Household Composition)**: Calculate persons, workers (ESR 1/4), income quintiles, and HHT (**X-H1**).
    4. **Step 4 (Dwelling Assignment)**: Carry dwellings for surviving; execute **D-H1** for new households. Compute POLARIS `type` (**X-H2**).
    5. **Step 5 (Home Change Events)**: Evaluate person home-change events against final locations.
    6. **Step 6 (Education & School)**: Assign `school_grade_level` (**X-P3..X-P5**), enforce K-12 consistency (**X-P6**), evaluate school change events.
    7. **Step 7 (Race)**: Assign heads of new households, then apply **D-P3b** for non-heads.
    8. **Step 8 (Job Attributes)**: Execute **D-P1** for workers needing employment details.
    9. **Step 9 (Commute Attributes)**: Execute **D-P2** for at-work commuters.
    10. **Step 10 (Locations & Models)**: Set `work_location_id`, `school_location_id`, disability (**D-P4**), and POLARIS runtime flags.
    11. **Step 11 (Vehicles)**: Map ATLAS fleet outputs via **X-V1..X-V5** (or **D-H2** interim); verify composite keys in `Vehicle_Type`.
    12. **Step 12 (Household Wrap-up)**: Update `time_in_home` and vehicle counts.
    13. **Step 13 (Output & Validation)**: Append unchanged Group Quarters, run integrity assertions, and emit final `Demand.sqlite`.

=== "Network Skims & Population Feedback Loop"

    ```mermaid
    sequenceDiagram
        autonumber
        participant OMX_In as InputNetworkSkims (.omx, Skim_t)
        participant US as UrbanSim (t to t+1)
        participant DEMOS as DEMOS (t to t+1)
        participant AT as ATLAS (t+1)
        participant POL as POLARIS (t+1)
        participant OMX_Out as NextYearNetworkSkims (.omx)

        Note over OMX_In,DEMOS: Year t Base Inputs
        OMX_In->>US: Zone Accessibility & Travel Impedance (Skim_t)
        US->>DEMOS: Block-Level Spatial Marginals (M_t+1)
        Note over DEMOS,POL: Year t+1 Evolution & Simulation
        DEMOS->>AT: Evolved Population (P_t+1 conforming with M_t+1)
        DEMOS->>POL: Evolved Household & Person Microdata (P_t+1)
        AT->>POL: Households with Vehicles & Vehicle Attributes
        US->>POL: Zonal Land Use & Employment Capacities
        Note over POL: Job/Household Tenure, Workplace, Activity, Mode & DTA
        POL->>OMX_Out: Emits Converged Travel Times & Skims (Year t+1)
        POL-->>DEMOS: Feedback to Next Iteration (POLARIS Population, P_t)
        OMX_Out-->>US: Feedback to Next Iteration (POLARIS Skim_t)
    ```

---

## 5. Multi-Team Interface Specification Workbook

The DEMOS (NLR), ATLAS (LBNL), and POLARIS (ANL) modeling teams maintain field-level formulas, donor stratification tables, and assumption logs (`A1` to `A31`) in the shared workbook:

- **File**: `docs/resources/DEMOS_and_ATLAS_to_POLARIS_interface.xlsx`
- **Contributors**: DEMOS (NLR), ATLAS (LBNL), and POLARIS (ANL) modeling teams.
- **Sheets**: `Overview`, `Households`, `Persons`, `Vehicles`, `Draws`, `Crosswalks`, `Assumptions`, `Open questions`, `Inputs`, `Record classes & events`, and `Process & settings`.
