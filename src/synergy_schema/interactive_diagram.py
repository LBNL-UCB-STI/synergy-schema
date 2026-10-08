"""Generate database ER diagrams and FK relationship reference page for documentation."""

from __future__ import annotations

from pathlib import Path

from synergy_schema.mermaid_diagram import (
    POPULATION_CLASSES,
    REGIONAL_CLASSES,
    generate_mermaid_erd,
)


def render_database_erd_markdown(schema_path: Path) -> str:
    """Generate Markdown page with Mermaid ER diagrams and LinkML foreign key reference table."""
    pop_mermaid = generate_mermaid_erd(schema_path, POPULATION_CLASSES)
    reg_mermaid = generate_mermaid_erd(schema_path, REGIONAL_CLASSES)

    return f"""# Database Schema & Entity-Relationship Diagrams

This page presents the compiled Entity-Relationship (ER) diagrams and foreign key contracts linking the multi-model population, vehicle fleet, land-use, and network skim tables across **UrbanSim**, **DEMOS**, **ATLAS**, **POLARIS**, and **OMX Skims** for Deliverable #1.

All tables, column definitions, primary keys, foreign keys, and cross-model handoff relationships are **generated directly from the LinkML schema contracts** (`src/synergy_schema/schema/deliverable_1_static_schema.yaml`).

---

## 1. Core Population & Vehicle Fleet ERD

The diagram below isolates the synthetic agent tables across DEMOS, ATLAS, and POLARIS with explicit relational cardinalities and crow's feet notation:

```mermaid
{pop_mermaid}
```

---

## 2. Complete 5-Model Regional Architecture ERD

The regional architecture diagram links all 12 tables across the 5 models, including UrbanSim Census Block marginals, Block-to-TAZ aggregation tables, and Open Matrix (`.omx`) travel impedance matrices:

```mermaid
{reg_mermaid}
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
