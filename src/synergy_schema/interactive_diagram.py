"""Generate database ER diagrams and FK relationship reference page for documentation."""

from __future__ import annotations

from pathlib import Path

from synergy_schema.mermaid_diagram import (
    BEAM_AS_REGIONAL_CLASSES,
    POLARIS_REGIONAL_CLASSES,
    POPULATION_CLASSES,
    REGIONAL_CLASSES,
    SPATIAL_SKIM_CLASSES,
    SYNTHFIRM_REGIONAL_CLASSES,
    generate_mermaid_erd,
)


def _indent(text: str, spaces: int = 4) -> str:
    """Indent all non-empty lines in text by the specified number of spaces."""
    prefix = " " * spaces
    return "\n".join(
        f"{prefix}{line}" if line.strip() else "" for line in text.splitlines()
    )


def render_database_erd_markdown(
    schema_path: Path,
    schema_prefix: str = "../schema",
) -> str:
    """Generate Markdown page with Mermaid ER diagrams and LinkML foreign key reference table."""
    pop_mermaid = generate_mermaid_erd(schema_path, POPULATION_CLASSES)
    reg_mermaid = generate_mermaid_erd(schema_path, REGIONAL_CLASSES)
    polaris_reg_mermaid = generate_mermaid_erd(schema_path, POLARIS_REGIONAL_CLASSES)
    beam_as_reg_mermaid = generate_mermaid_erd(schema_path, BEAM_AS_REGIONAL_CLASSES)
    spatial_skim_mermaid = generate_mermaid_erd(schema_path, SPATIAL_SKIM_CLASSES)
    synthfirm_reg_mermaid = generate_mermaid_erd(
        schema_path, SYNTHFIRM_REGIONAL_CLASSES
    )

    reg_indented = _indent(reg_mermaid, 4)
    polaris_indented = _indent(polaris_reg_mermaid, 4)
    beam_as_indented = _indent(beam_as_reg_mermaid, 4)
    spatial_skim_indented = _indent(spatial_skim_mermaid, 4)
    synthfirm_indented = _indent(synthfirm_reg_mermaid, 4)

    return f"""# Database Schema & Entity-Relationship Diagrams

This page presents the compiled Entity-Relationship (ER) diagrams and foreign key contracts linking the multi-model population, vehicle fleet, land-use, freight commodity flows, and network skim tables across **UrbanSim**, **DEMOS**, **ATLAS**, **POLARIS**, **ActivitySim**, **BEAM**, **SynthFirm**, and **OMX Skims** for Deliverable #1.

All tables, column definitions, primary keys, foreign keys, and cross-model handoff relationships are **generated directly from the LinkML schema contracts** (`schema/deliverable_1_static_schema.yaml`).

---

## 1. Core Population & Vehicle Fleet ERD

The diagram below isolates the synthetic agent tables across DEMOS, ATLAS, and POLARIS with explicit relational cardinalities and crow's feet notation:

```mermaid
{pop_mermaid}
```

---

## 2. Complete Multi-Model Regional Architecture ERD

The regional architecture diagrams link the tables across the modeling suite. To provide both a unified multi-tier architecture and focused subsystem layouts that fit comfortably on vertical viewports without horizontal sprawl, four tabbed perspectives are provided:

=== "Complete Regional Architecture (Cascaded Vertical Flow)"

    ```mermaid
{reg_indented}
    ```

=== "Primary POLARIS Regional Flow"

    ```mermaid
{polaris_indented}
    ```

=== "ActivitySim & BEAM Multi-Agent Flow"

    ```mermaid
{beam_as_indented}
    ```

=== "Spatial Aggregation & Skim Feedback"

    ```mermaid
{spatial_skim_indented}
    ```

=== "SynthFirm Freight & Commercial Flow"

    ```mermaid
{synthfirm_indented}
    ```


---

## 3. Foreign Key & Pipeline Linkage Reference Table

The table below documents every intra-model foreign key and cross-model handoff contract compiled from the schema:

| Child Table | Child Column | Parent Table | Parent Column | Cardinality | Link Type | Pipeline Purpose |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- |
| [`BlockToTazMapping`]({schema_prefix}/BlockToTazMapping.md) | `block_id` `[FK]` | [`UrbanSimBlockMarginals`]({schema_prefix}/UrbanSimBlockMarginals.md) | `block_id` `[PK]` | $N:1$ | Intra-Model FK | Associates Census Blocks with regional marginal controls |
| [`BlockToTazMapping`]({schema_prefix}/BlockToTazMapping.md) | `zone_id` `[FK]` | [`UrbanSimZonalTotals`]({schema_prefix}/UrbanSimZonalTotals.md) | `zone_id` `[PK]` | $N:1$ | Intra-Model FK | Maps Census Blocks into POLARIS-compatible TAZ zones |
| [`DemosPolarisMappedPerson`]({schema_prefix}/DemosPolarisMappedPerson.md) | `household` `[FK]` | [`DemosPolarisMappedHousehold`]({schema_prefix}/DemosPolarisMappedHousehold.md) | `household` `[PK]` | $N:1$ | Intra-Model FK | Enforces person membership in synthetic households |
| [`AtlasVehicleFleetOutput`]({schema_prefix}/AtlasVehicleFleetOutput.md) | `houseid` `[FK]` | [`AtlasHouseholdFleetOutput`]({schema_prefix}/AtlasHouseholdFleetOutput.md) | `houseid` `[PK]` | $N:1$ | Intra-Model FK | Associates discrete vehicles with synthesized household fleets |
| [`PolarisDemandDatabasePerson`]({schema_prefix}/PolarisDemandDatabasePerson.md) | `household` `[FK]` | [`PolarisDemandDatabaseHousehold`]({schema_prefix}/PolarisDemandDatabaseHousehold.md) | `household` `[PK]` | $N:1$ | Intra-Model FK | Enforces POLARIS traveler membership in households |
| [`PolarisDemandDatabaseVehicle`]({schema_prefix}/PolarisDemandDatabaseVehicle.md) | `hhold` `[FK]` | [`PolarisDemandDatabaseHousehold`]({schema_prefix}/PolarisDemandDatabaseHousehold.md) | `household` `[PK]` | $N:1$ | Intra-Model FK | Associates POLARIS vehicles with households |
| [`AtlasHouseholdFleetOutput`]({schema_prefix}/AtlasHouseholdFleetOutput.md) | `houseid` `[FK]` | [`DemosPolarisMappedHousehold`]({schema_prefix}/DemosPolarisMappedHousehold.md) | `household` `[PK]` | $1:1$ | Cross-Model Join | Joins ATLAS synthesized vehicle counts to DEMOS households |
| [`PolarisDemandDatabaseHousehold`]({schema_prefix}/PolarisDemandDatabaseHousehold.md) | `household` `[FK]` | [`DemosPolarisMappedHousehold`]({schema_prefix}/DemosPolarisMappedHousehold.md) | `household` `[PK]` | $1:1$ | Cross-Model Lineage | Lineage tracking from DEMOS base population to POLARIS demand |
| [`PolarisDemandDatabasePerson`]({schema_prefix}/PolarisDemandDatabasePerson.md) | `person` `[FK]` | [`DemosPolarisMappedPerson`]({schema_prefix}/DemosPolarisMappedPerson.md) | `person` `[PK]` | $1:1$ | Cross-Model Lineage | Lineage tracking & direct attribute translation from DEMOS synthetic persons to POLARIS demand persons |
| [`PolarisDemandDatabaseVehicle`]({schema_prefix}/PolarisDemandDatabaseVehicle.md) | `vehicle_id` `[FK]` | [`AtlasVehicleFleetOutput`]({schema_prefix}/AtlasVehicleFleetOutput.md) | `vehid` `[PK]` | $1:1$ | Cross-Model Lineage | Recodes ATLAS discrete vehicles to POLARIS vehicle types |
| [`PolarisDemandDatabaseHousehold`]({schema_prefix}/PolarisDemandDatabaseHousehold.md) | `location` `[FK]` | [`UrbanSimZonalTotals`]({schema_prefix}/UrbanSimZonalTotals.md) | `zone_id` `[PK]` | $N:1$ | Cross-Model Spatial | Assigns household residence to UrbanSim TAZ zones |
| [`DemosPolarisMappedHousehold`]({schema_prefix}/DemosPolarisMappedHousehold.md) | `block_id` `[FK]` | [`UrbanSimBlockMarginals`]({schema_prefix}/UrbanSimBlockMarginals.md) | `block_id` `[PK]` | $N:1$ | Cross-Model Spatial | Controls demographic synthesis by Census Block marginals |
| [`InputNetworkSkims`]({schema_prefix}/InputNetworkSkims.md) | `zone_count` `[FK]` | [`UrbanSimZonalTotals`]({schema_prefix}/UrbanSimZonalTotals.md) | `zone_id` `[PK]` | $N:1$ | Cross-Model Spatial | Confirms skim matrix dimensions match active TAZ zones |
| [`NextYearNetworkSkims`]({schema_prefix}/NextYearNetworkSkims.md) | `zone_count` `[FK]` | [`UrbanSimZonalTotals`]({schema_prefix}/UrbanSimZonalTotals.md) | `zone_id` `[PK]` | $N:1$ | Cross-Model Spatial | Confirms iterative skim matrix dimensions match active TAZ zones |
| [`ActivitySimPersonInputRecord`]({schema_prefix}/ActivitySimPersonInputRecord.md) | `household_id` `[FK]` | [`ActivitySimHouseholdInputRecord`]({schema_prefix}/ActivitySimHouseholdInputRecord.md) | `household_id` `[PK]` | $N:1$ | Intra-Model FK | Enforces person membership in ActivitySim households |
| [`ActivitySimHouseholdInputRecord`]({schema_prefix}/ActivitySimHouseholdInputRecord.md) | `TAZ` `[FK]` | [`UrbanSimZonalTotals`]({schema_prefix}/UrbanSimZonalTotals.md) | `zone_id` `[PK]` | $N:1$ | Cross-Model Spatial | Associates ActivitySim household residence with TAZ zones |
| [`ActivitySimHouseholdInputRecord`]({schema_prefix}/ActivitySimHouseholdInputRecord.md) | `block_id` `[FK]` | [`UrbanSimBlockMarginals`]({schema_prefix}/UrbanSimBlockMarginals.md) | `block_id` `[PK]` | $N:1$ | Cross-Model Spatial | Anchors ActivitySim households to Census Block marginals |
| [`ActivitySimHouseholdInputRecord`]({schema_prefix}/ActivitySimHouseholdInputRecord.md) | `cars` `[FK]` | [`AtlasHouseholdFleetOutput`]({schema_prefix}/AtlasHouseholdFleetOutput.md) | `houseid` `[PK]` | $1:1$ | Cross-Model Update | Updates household car count (`cars`) from ATLAS vehicle ownership (`nvehicles`) for mode choice |
| [`ActivitySimHouseholdInputRecord`]({schema_prefix}/ActivitySimHouseholdInputRecord.md) | `household_id` `[FK]` | [`DemosPolarisMappedHousehold`]({schema_prefix}/DemosPolarisMappedHousehold.md) | `household` `[PK]` | $1:1$ | Cross-Model Lineage | Lineage tracking from DEMOS base population to ActivitySim |
| [`ActivitySimPersonInputRecord`]({schema_prefix}/ActivitySimPersonInputRecord.md) | `person_id` `[FK]` | [`DemosPolarisMappedPerson`]({schema_prefix}/DemosPolarisMappedPerson.md) | `person` `[PK]` | $1:1$ | Cross-Model Lineage | Lineage tracking from DEMOS synthetic persons to ActivitySim |
| [`BeamPersonRecord`]({schema_prefix}/BeamPersonRecord.md) | `household_id` `[FK]` | [`BeamHouseholdRecord`]({schema_prefix}/BeamHouseholdRecord.md) | `household_id` `[PK]` | $N:1$ | Intra-Model FK | Enforces person membership in BEAM simulated households |
| [`BeamVehicleRecord`]({schema_prefix}/BeamVehicleRecord.md) | `household_id` `[FK]` | [`BeamHouseholdRecord`]({schema_prefix}/BeamHouseholdRecord.md) | `household_id` `[PK]` | $N:1$ | Intra-Model FK | Associates BEAM staged vehicles with households |
| [`BeamVehicleRecord`]({schema_prefix}/BeamVehicleRecord.md) | `maindriver_id` `[FK]` | [`BeamPersonRecord`]({schema_prefix}/BeamPersonRecord.md) | `person_id` `[PK]` | $N:1$ | Intra-Model FK | Assigns primary driver to household vehicle |
| [`BeamPlanRecord`]({schema_prefix}/BeamPlanRecord.md) | `person_id` `[FK]` | [`BeamPersonRecord`]({schema_prefix}/BeamPersonRecord.md) | `person_id` `[PK]` | $N:1$ | Intra-Model FK | Sequences activity elements and legs for simulated agent |
| [`BeamPlanRecord`]({schema_prefix}/BeamPlanRecord.md) | `person_id` `[FK]` | [`ActivitySimPersonInputRecord`]({schema_prefix}/ActivitySimPersonInputRecord.md) | `person_id` `[PK]` | $N:1$ | Cross-Model Schedule | Populates BEAM agent travel plans from ActivitySim schedule |
| [`BeamHouseholdRecord`]({schema_prefix}/BeamHouseholdRecord.md) | `household_id` `[FK]` | [`DemosPolarisMappedHousehold`]({schema_prefix}/DemosPolarisMappedHousehold.md) | `household` `[PK]` | $1:1$ | Cross-Model Lineage | Lineage tracking from DEMOS base population to BEAM agents |
| [`BeamPersonRecord`]({schema_prefix}/BeamPersonRecord.md) | `person_id` `[FK]` | [`DemosPolarisMappedPerson`]({schema_prefix}/DemosPolarisMappedPerson.md) | `person` `[PK]` | $1:1$ | Cross-Model Lineage | Lineage tracking from DEMOS synthetic persons to BEAM agents |
| [`BeamVehicleRecord`]({schema_prefix}/BeamVehicleRecord.md) | `vehicle_id` `[FK]` | [`AtlasVehicleFleetOutput`]({schema_prefix}/AtlasVehicleFleetOutput.md) | `vehid` `[PK]` | $1:1$ | Cross-Model Lineage | Stages ATLAS vehicle fleet with powertrains into BEAM |
| [`BeamHouseholdRecord`]({schema_prefix}/BeamHouseholdRecord.md) | `home_zone_id` `[FK]` | [`UrbanSimZonalTotals`]({schema_prefix}/UrbanSimZonalTotals.md) | `zone_id` `[PK]` | $N:1$ | Cross-Model Spatial | Places BEAM households in regional TAZ zones |
| [`BeamHouseholdRecord`]({schema_prefix}/BeamHouseholdRecord.md) | `block_id` `[FK]` | [`UrbanSimBlockMarginals`]({schema_prefix}/UrbanSimBlockMarginals.md) | `block_id` `[PK]` | $N:1$ | Cross-Model Spatial | Anchors BEAM agents to Census Block marginals |
| [`BeamNetworkSkims`]({schema_prefix}/BeamNetworkSkims.md) | `zone_count` `[FK]` | [`UrbanSimZonalTotals`]({schema_prefix}/UrbanSimZonalTotals.md) | `zone_id` `[PK]` | $N:1$ | Cross-Model Spatial | Confirms BEAM multi-modal skim matrix dimensions match active TAZ zones |
| [`SynthFirmEstablishmentRecord`]({schema_prefix}/SynthFirmEstablishmentRecord.md) | `MESOZONE` `[FK]` | [`UrbanSimBlockMarginals`]({schema_prefix}/UrbanSimBlockMarginals.md) | `block_id` `[PK]` | $N:1$ | Cross-Model Spatial | Anchors synthetic establishment to Census Block Group / marginal employment |
| [`SynthFirmCarrierRecord`]({schema_prefix}/SynthFirmCarrierRecord.md) | `BusID` `[PK, FK]` | [`SynthFirmEstablishmentRecord`]({schema_prefix}/SynthFirmEstablishmentRecord.md) | `BusID` `[PK]` | $1:1$ | Subtype Specialization | Specializes business establishment as for-hire commercial trucking carrier |
| [`SynthFirmB2BShipmentRecord`]({schema_prefix}/SynthFirmB2BShipmentRecord.md) | `BuyerID` `[FK]` | [`SynthFirmEstablishmentRecord`]({schema_prefix}/SynthFirmEstablishmentRecord.md) | `BusID` `[PK]` | $N:1$ | Intra-Model FK | Identifies buyer establishment for B2B commodity shipment |
| [`SynthFirmB2BShipmentRecord`]({schema_prefix}/SynthFirmB2BShipmentRecord.md) | `SellerID` `[FK]` | [`SynthFirmEstablishmentRecord`]({schema_prefix}/SynthFirmEstablishmentRecord.md) | `BusID` `[PK]` | $N:1$ | Intra-Model FK | Identifies origin shipper establishment for B2B commodity shipment |
| [`SynthFirmB2BShipmentRecord`]({schema_prefix}/SynthFirmB2BShipmentRecord.md) | `fleet_id` `[FK]` | [`SynthFirmEstablishmentRecord`]({schema_prefix}/SynthFirmEstablishmentRecord.md) | `fleet_id` `[FK]` | $N:1$ | Intra-Model FK | Associates private truck shipment with seller's private fleet allocation |
| [`SynthFirmInternationalFreightRecord`]({schema_prefix}/SynthFirmInternationalFreightRecord.md) | `BuyerID` `[FK]` | [`SynthFirmEstablishmentRecord`]({schema_prefix}/SynthFirmEstablishmentRecord.md) | `BusID` `[PK]` | $N:1$ | Intra-Model FK | Connects port/airport import drayage flow to domestic buyer |
| [`SynthFirmInternationalFreightRecord`]({schema_prefix}/SynthFirmInternationalFreightRecord.md) | `SellerID` `[FK]` | [`SynthFirmEstablishmentRecord`]({schema_prefix}/SynthFirmEstablishmentRecord.md) | `BusID` `[PK]` | $N:1$ | Intra-Model FK | Connects domestic seller to port/airport export drayage flow |
| [`PolarisDemandDatabaseVehicle`]({schema_prefix}/PolarisDemandDatabaseVehicle.md) | `vehicle_id` `[FK]` | [`SynthFirmEstablishmentRecord`]({schema_prefix}/SynthFirmEstablishmentRecord.md) | `BusID` `[PK]` | $N:1$ | Cross-Model Fleet | Stages SynthFirm commercial vehicle fleet into POLARIS commercial vehicle demand |
| [`BeamVehicleRecord`]({schema_prefix}/BeamVehicleRecord.md) | `vehicle_id` `[FK]` | [`SynthFirmEstablishmentRecord`]({schema_prefix}/SynthFirmEstablishmentRecord.md) | `BusID` `[PK]` | $N:1$ | Cross-Model Fleet | Stages SynthFirm commercial trucks into BEAM freight agent fleet |
"""


def render_interactive_markdown(
    schema_path: Path,
    js_src: str = "",
    schema_prefix: str = "../schema",
) -> str:
    """Backwards-compatible alias for render_database_erd_markdown."""
    return render_database_erd_markdown(schema_path, schema_prefix=schema_prefix)


def generate_interactive_diagram(
    schema_path: Path | None = None,
    output_path: Path | None = None,
    js_src: str = "",
    schema_prefix: str = "../schema",
) -> Path:
    """Generate and write database ER diagram documentation page."""
    base_dir = Path(__file__).resolve().parents[2]
    if schema_path is None:
        schema_path = (
            base_dir
            / "src"
            / "synergy_schema"
            / "schema"
            / "deliverable_1_static_schema.yaml"
        )
    if output_path is None:
        output_path = (
            base_dir / "docs" / "cross-model-mappings" / "interactive-schema.md"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = render_database_erd_markdown(schema_path, schema_prefix=schema_prefix)
    output_path.write_text(content, encoding="utf-8")
    return output_path


if __name__ == "__main__":
    out = generate_interactive_diagram()
    print(f"Generated Database ERD documentation page at: {out}")
