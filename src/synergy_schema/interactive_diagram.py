"""Generate database ER diagrams and FK relationship reference page for documentation."""

from __future__ import annotations

from pathlib import Path

from synergy_schema.mermaid_diagram import (
    BEAM_AS_REGIONAL_CLASSES,
    POLARIS_REGIONAL_CLASSES,
    POPULATION_CLASSES,
    REGIONAL_CLASSES,
    SPATIAL_SKIM_CLASSES,
    generate_mermaid_erd,
)


def _indent(text: str, spaces: int = 4) -> str:
    """Indent all non-empty lines in text by the specified number of spaces."""
    prefix = " " * spaces
    return "\n".join(
        f"{prefix}{line}" if line.strip() else "" for line in text.splitlines()
    )


def render_database_erd_markdown(schema_path: Path) -> str:
    """Generate Markdown page with Mermaid ER diagrams and LinkML foreign key reference table."""
    pop_mermaid = generate_mermaid_erd(schema_path, POPULATION_CLASSES)
    reg_mermaid = generate_mermaid_erd(schema_path, REGIONAL_CLASSES)
    polaris_reg_mermaid = generate_mermaid_erd(schema_path, POLARIS_REGIONAL_CLASSES)
    beam_as_reg_mermaid = generate_mermaid_erd(schema_path, BEAM_AS_REGIONAL_CLASSES)
    spatial_skim_mermaid = generate_mermaid_erd(schema_path, SPATIAL_SKIM_CLASSES)

    reg_indented = _indent(reg_mermaid, 4)
    polaris_indented = _indent(polaris_reg_mermaid, 4)
    beam_as_indented = _indent(beam_as_reg_mermaid, 4)
    spatial_skim_indented = _indent(spatial_skim_mermaid, 4)

    return f"""# Database Schema & Entity-Relationship Diagrams

This page presents the compiled Entity-Relationship (ER) diagrams and foreign key contracts linking the multi-model population, vehicle fleet, land-use, and network skim tables across **UrbanSim**, **DEMOS**, **ATLAS**, **POLARIS**, **ActivitySim**, **BEAM**, and **OMX Skims** for Deliverable #1.

All tables, column definitions, primary keys, foreign keys, and cross-model handoff relationships are **generated directly from the LinkML schema contracts** (`src/synergy_schema/schema/deliverable_1_static_schema.yaml`).

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


---

## 3. Foreign Key & Pipeline Linkage Reference Table

The table below documents every intra-model foreign key and cross-model handoff contract compiled from the schema:

| Child Table | Child Column | Parent Table | Parent Column | Cardinality | Link Type | Pipeline Purpose |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- |
| `BlockToTazMapping` | `block_id` `[FK]` | `UrbanSimBlockMarginals` | `block_id` `[PK]` | $N:1$ | Intra-Model FK | Associates Census Blocks with regional marginal controls |
| `BlockToTazMapping` | `zone_id` `[FK]` | `UrbanSimZonalTotals` | `zone_id` `[PK]` | $N:1$ | Intra-Model FK | Maps Census Blocks into POLARIS-compatible TAZ zones |
| `DemosPolarisMappedPerson` | `household` `[FK]` | `DemosPolarisMappedHousehold` | `household` `[PK]` | $N:1$ | Intra-Model FK | Enforces person membership in synthetic households |
| `AtlasVehicleFleetOutput` | `houseid` `[FK]` | `AtlasHouseholdFleetOutput` | `houseid` `[PK]` | $N:1$ | Intra-Model FK | Associates discrete vehicles with synthesized household fleets |
| `PolarisDemandDatabasePerson` | `household` `[FK]` | `PolarisDemandDatabaseHousehold` | `household` `[PK]` | $N:1$ | Intra-Model FK | Enforces POLARIS traveler membership in households |
| `PolarisDemandDatabaseVehicle` | `hhold` `[FK]` | `PolarisDemandDatabaseHousehold` | `household` `[PK]` | $N:1$ | Intra-Model FK | Associates POLARIS vehicles with households |
| `AtlasHouseholdFleetOutput` | `houseid` `[FK]` | `DemosPolarisMappedHousehold` | `household` `[PK]` | $1:1$ | Cross-Model Join | Joins ATLAS synthesized vehicle counts to DEMOS households |
| `PolarisDemandDatabaseHousehold` | `household` `[FK]` | `DemosPolarisMappedHousehold` | `household` `[PK]` | $1:1$ | Cross-Model Lineage | Lineage tracking from DEMOS base population to POLARIS demand |
| `PolarisDemandDatabaseVehicle` | `vehicle_id` `[FK]` | `AtlasVehicleFleetOutput` | `vehid` `[PK]` | $1:1$ | Cross-Model Lineage | Recodes ATLAS discrete vehicles to POLARIS vehicle types |
| `PolarisDemandDatabaseHousehold` | `location` `[FK]` | `UrbanSimZonalTotals` | `zone_id` `[PK]` | $N:1$ | Cross-Model Spatial | Assigns household residence to UrbanSim TAZ zones |
| `DemosPolarisMappedHousehold` | `block_id` `[FK]` | `UrbanSimBlockMarginals` | `block_id` `[PK]` | $N:1$ | Cross-Model Spatial | Controls demographic synthesis by Census Block marginals |
| `InputNetworkSkims` | `zone_count` `[FK]` | `UrbanSimZonalTotals` | `zone_id` `[PK]` | $N:1$ | Cross-Model Spatial | Confirms skim matrix dimensions match active TAZ zones |
| `NextYearNetworkSkims` | `zone_count` `[FK]` | `UrbanSimZonalTotals` | `zone_id` `[PK]` | $N:1$ | Cross-Model Spatial | Confirms iterative skim matrix dimensions match active TAZ zones |
| `NextYearNetworkSkims` | `zone_count` `[FK]` | `PolarisDemandDatabaseVehicle` | `vehicle_id` `[PK]` | $N:1$ | Cross-Model Simulation | Dynamic traffic assignment simulates next-year travel skims |
| `ActivitySimPersonInputRecord` | `household_id` `[FK]` | `ActivitySimHouseholdInputRecord` | `household_id` `[PK]` | $N:1$ | Intra-Model FK | Enforces person membership in ActivitySim households |
| `ActivitySimHouseholdInputRecord` | `TAZ` `[FK]` | `UrbanSimZonalTotals` | `zone_id` `[PK]` | $N:1$ | Cross-Model Spatial | Associates ActivitySim household residence with TAZ zones |
| `ActivitySimHouseholdInputRecord` | `block_id` `[FK]` | `UrbanSimBlockMarginals` | `block_id` `[PK]` | $N:1$ | Cross-Model Spatial | Anchors ActivitySim households to Census Block marginals |
| `ActivitySimHouseholdInputRecord` | `cars` `[FK]` | `AtlasHouseholdFleetOutput` | `houseid` `[PK]` | $1:1$ | Cross-Model Update | Updates household car count (`cars`) from ATLAS vehicle ownership (`nvehicles`) for mode choice |
| `ActivitySimHouseholdInputRecord` | `household_id` `[FK]` | `DemosPolarisMappedHousehold` | `household` `[PK]` | $1:1$ | Cross-Model Lineage | Lineage tracking from DEMOS base population to ActivitySim |
| `BeamPersonRecord` | `household_id` `[FK]` | `BeamHouseholdRecord` | `household_id` `[PK]` | $N:1$ | Intra-Model FK | Enforces person membership in BEAM simulated households |
| `BeamVehicleRecord` | `household_id` `[FK]` | `BeamHouseholdRecord` | `household_id` `[PK]` | $N:1$ | Intra-Model FK | Associates BEAM staged vehicles with households |
| `BeamVehicleRecord` | `maindriver_id` `[FK]` | `BeamPersonRecord` | `person_id` `[PK]` | $N:1$ | Intra-Model FK | Assigns primary driver to household vehicle |
| `BeamPlanRecord` | `person_id` `[FK]` | `BeamPersonRecord` | `person_id` `[PK]` | $N:1$ | Intra-Model FK | Sequences activity elements and legs for simulated agent |
| `BeamPlanRecord` | `person_id` `[FK]` | `ActivitySimPersonInputRecord` | `person_id` `[PK]` | $1:1$ | Cross-Model Schedule | Populates BEAM agent travel plans from ActivitySim schedule |
| `BeamHouseholdRecord` | `household_id` `[FK]` | `DemosPolarisMappedHousehold` | `household` `[PK]` | $1:1$ | Cross-Model Lineage | Lineage tracking from DEMOS base population to BEAM agents |
| `BeamVehicleRecord` | `vehicle_id` `[FK]` | `AtlasVehicleFleetOutput` | `vehid` `[PK]` | $1:1$ | Cross-Model Lineage | Stages ATLAS vehicle fleet with powertrains into BEAM |
| `BeamHouseholdRecord` | `home_zone_id` `[FK]` | `UrbanSimZonalTotals` | `zone_id` `[PK]` | $N:1$ | Cross-Model Spatial | Places BEAM households in regional TAZ zones |
| `BeamHouseholdRecord` | `block_id` `[FK]` | `UrbanSimBlockMarginals` | `block_id` `[PK]` | $N:1$ | Cross-Model Spatial | Anchors BEAM agents to Census Block marginals |
| `BeamNetworkSkims` | `zone_count` `[FK]` | `UrbanSimZonalTotals` | `zone_id` `[PK]` | $N:1$ | Cross-Model Spatial | Confirms BEAM multi-modal skim matrix dimensions match active TAZ zones |
| `BeamNetworkSkims` | `zone_count` `[FK]` | `BeamPlanRecord` | `plan_id` `[PK]` | $N:1$ | Cross-Model Simulation | BEAM multi-agent dynamic simulation produces converged skim matrices |
"""


def render_interactive_markdown(
    schema_path: Path,
    js_src: str = "",
) -> str:
    """Backwards-compatible alias for render_database_erd_markdown."""
    return render_database_erd_markdown(schema_path)


def generate_interactive_diagram(
    schema_path: Path | None = None,
    output_path: Path | None = None,
    js_src: str = "",
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
    content = render_database_erd_markdown(schema_path)
    output_path.write_text(content, encoding="utf-8")
    return output_path


if __name__ == "__main__":
    out = generate_interactive_diagram()
    print(f"Generated Database ERD documentation page at: {out}")
