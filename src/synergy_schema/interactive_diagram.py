"""Generate interactive, zoomable population database diagram from LinkML schema for Zensical documentation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from linkml_runtime.utils.schemaview import SchemaView

from synergy_schema.mermaid_diagram import (
    generate_mermaid_erd,
    POPULATION_CLASSES,
    REGIONAL_CLASSES,
)

# Default table layout positions in the 2D coordinate space (pixels)
TABLE_POSITIONS: dict[str, dict[str, int]] = {
    # Exogenous / Network Skims (Left / Top)
    "InputNetworkSkims": {"x": 40, "y": 60, "width": 310},
    "NextYearNetworkSkims": {"x": 40, "y": 550, "width": 310},
    # UrbanSim (Top Center)
    "UrbanSimBlockMarginals": {"x": 420, "y": 60, "width": 320},
    "BlockToTazMapping": {"x": 780, "y": 60, "width": 280},
    "UrbanSimZonalTotals": {"x": 1100, "y": 60, "width": 310},
    # DEMOS (Middle Left / Center)
    "DemosPolarisMappedHousehold": {"x": 420, "y": 520, "width": 320},
    "DemosPolarisMappedPerson": {"x": 780, "y": 520, "width": 310},
    # ATLAS (Middle Right)
    "AtlasHouseholdFleetOutput": {"x": 1130, "y": 480, "width": 290},
    "AtlasVehicleFleetOutput": {"x": 1130, "y": 680, "width": 290},
    # POLARIS Demand (Bottom Center / Right)
    "PolarisDemandDatabaseHousehold": {"x": 580, "y": 980, "width": 320},
    "PolarisDemandDatabasePerson": {"x": 940, "y": 980, "width": 290},
    "PolarisDemandDatabaseVehicle": {"x": 1270, "y": 980, "width": 290},
}

MODEL_METADATA: dict[str, dict[str, str]] = {
    "UrbanSim": {
        "color": "#0284c7",
        "bg": "#0369a1",
        "border": "#38bdf8",
        "badge": "UrbanSim Land Use",
    },
    "DEMOS": {
        "color": "#10b981",
        "bg": "#059669",
        "border": "#34d399",
        "badge": "DEMOS Synthesis",
    },
    "ATLAS": {
        "color": "#f59e0b",
        "bg": "#d97706",
        "border": "#fbbf24",
        "badge": "ATLAS Fleet",
    },
    "POLARIS": {
        "color": "#8b5cf6",
        "bg": "#7c3aed",
        "border": "#a78bfa",
        "badge": "POLARIS Demand/Supply",
    },
    "Skims": {
        "color": "#ec4899",
        "bg": "#db2777",
        "border": "#f472b6",
        "badge": "Network Skims (.omx)",
    },
}

CLASS_TO_MODEL: dict[str, str] = {
    "UrbanSimBlockMarginals": "UrbanSim",
    "BlockToTazMapping": "UrbanSim",
    "UrbanSimZonalTotals": "UrbanSim",
    "DemosPolarisMappedHousehold": "DEMOS",
    "DemosPolarisMappedPerson": "DEMOS",
    "AtlasHouseholdFleetOutput": "ATLAS",
    "AtlasVehicleFleetOutput": "ATLAS",
    "PolarisDemandDatabaseHousehold": "POLARIS",
    "PolarisDemandDatabasePerson": "POLARIS",
    "PolarisDemandDatabaseVehicle": "POLARIS",
    "InputNetworkSkims": "Skims",
    "NextYearNetworkSkims": "Skims",
}

# Explicit multi-model handoff channels from Deliverable 1 contracts
CROSS_MODEL_CHANNELS = [
    {
        "channel_id": "C-U1",
        "source": "UrbanSimBlockMarginals",
        "source_col": "block_id",
        "target": "DemosPolarisMappedHousehold",
        "target_col": "block_id",
        "label": "C-U1: Block Controls",
        "description": "Zonal and Census Block marginal populations feed synthetic household creation.",
        "color": "#38bdf8",
    },
    {
        "channel_id": "C-D1",
        "source": "DemosPolarisMappedHousehold",
        "source_col": "household",
        "target": "AtlasHouseholdFleetOutput",
        "target_col": "houseid",
        "label": "C-D1: Household Identity",
        "description": "Deterministic 1-to-1 household identifier handoff from DEMOS to ATLAS.",
        "color": "#10b981",
    },
    {
        "channel_id": "C-D2_HH",
        "source": "DemosPolarisMappedHousehold",
        "source_col": "household",
        "target": "PolarisDemandDatabaseHousehold",
        "target_col": "household",
        "label": "C-D2: HH Demand",
        "description": "DEMOS household demographics mapped to POLARIS Demand.sqlite Household table.",
        "color": "#10b981",
    },
    {
        "channel_id": "C-D2_P",
        "source": "DemosPolarisMappedPerson",
        "source_col": "person",
        "target": "PolarisDemandDatabasePerson",
        "target_col": "person",
        "label": "C-D2: Person Demand",
        "description": "DEMOS person microdata mapped to POLARIS Demand.sqlite Person table with crosswalks.",
        "color": "#34d399",
    },
    {
        "channel_id": "C-A1",
        "source": "AtlasVehicleFleetOutput",
        "source_col": "houseid",
        "target": "PolarisDemandDatabaseVehicle",
        "target_col": "hhold",
        "label": "C-A1: Vehicle Fleet",
        "description": "ATLAS synthesized vehicle inventory and powertrains mapped to POLARIS Vehicle table.",
        "color": "#f59e0b",
    },
    {
        "channel_id": "C-U2",
        "source": "UrbanSimZonalTotals",
        "source_col": "zone_id",
        "target": "PolarisDemandDatabaseHousehold",
        "target_col": "location",
        "label": "C-U2: Zonal Allocation",
        "description": "Aggregated TAZ land use and capacities establish POLARIS spatial locations.",
        "color": "#0284c7",
    },
    {
        "channel_id": "C-P2_US",
        "source": "InputNetworkSkims",
        "source_col": "sov_time_am",
        "target": "UrbanSimBlockMarginals",
        "target_col": "block_id",
        "label": "C-P2: Accessibility Logsums",
        "description": "Prior-year highway travel times and distances feed land-use real estate models.",
        "color": "#ec4899",
    },
    {
        "channel_id": "C-P3",
        "source": "PolarisDemandDatabaseVehicle",
        "source_col": "vehicle_id",
        "target": "NextYearNetworkSkims",
        "target_col": "file_path",
        "label": "C-P3: DTA Simulation Skims",
        "description": "POLARIS Dynamic Traffic Assignment outputs next-year network skims for next cycle.",
        "color": "#a855f7",
    },
]


def extract_schema_graph(schema_path: Path) -> dict[str, Any]:
    """Inspect LinkML schema using SchemaView and extract tables, columns, and relationships."""
    sv = SchemaView(str(schema_path))
    tables = []

    for cls_name, pos in TABLE_POSITIONS.items():
        cls = sv.get_class(cls_name)
        if not cls:
            continue

        model_name = CLASS_TO_MODEL.get(cls_name, "Other")
        slots = sv.class_induced_slots(cls_name)

        columns = []
        for s in slots:
            ann = getattr(s, "annotations", {})

            # Extract FK from LinkML annotations
            fk_target = None
            if hasattr(ann, "__getitem__"):
                try:
                    if "foreign_key" in ann:
                        val = ann["foreign_key"]
                        fk_target = val.value if hasattr(val, "value") else str(val)
                    elif "relationship_target" in ann:
                        val = ann["relationship_target"]
                        fk_target = val.value if hasattr(val, "value") else str(val)
                except Exception:
                    pass

            # Extract crosswalk ID
            crosswalk_id = None
            if hasattr(ann, "__getitem__"):
                try:
                    if "crosswalk" in ann:
                        val = ann["crosswalk"]
                        crosswalk_id = val.value if hasattr(val, "value") else str(val)
                except Exception:
                    pass

            is_pk = bool(s.identifier or s.key)

            columns.append(
                {
                    "name": s.name,
                    "type": str(s.range),
                    "required": bool(s.required),
                    "pk": is_pk,
                    "fk": fk_target,
                    "crosswalk": crosswalk_id,
                    "description": s.description or "",
                }
            )

        alias = cls.aliases[0] if cls.aliases else cls_name
        tables.append(
            {
                "id": cls_name,
                "name": cls_name,
                "alias": alias,
                "model": model_name,
                "description": cls.description or "",
                "x": pos["x"],
                "y": pos["y"],
                "width": pos["width"],
                "columns": columns,
            }
        )

    # Intra-model foreign key edges extracted directly from LinkML annotations
    edges = []
    for t in tables:
        for col in t["columns"]:
            if col["fk"]:
                fk_parts = col["fk"].split(".")
                target_table = fk_parts[0]
                target_col = fk_parts[1] if len(fk_parts) > 1 else ""
                edges.append(
                    {
                        "id": f"{t['id']}_{col['name']}_to_{target_table}",
                        "source": t["id"],
                        "source_col": col["name"],
                        "target": target_table,
                        "target_col": target_col,
                        "label": f"FK: {col['name']}",
                        "type": "intra_model_fk",
                        "color": MODEL_METADATA.get(t["model"], {}).get(
                            "color", "#64748b"
                        ),
                        "dashed": False,
                    }
                )

    # Add cross-model handoff channels
    for ch in CROSS_MODEL_CHANNELS:
        edges.append(
            {
                "id": ch["channel_id"],
                "source": ch["source"],
                "source_col": ch["source_col"],
                "target": ch["target"],
                "target_col": ch["target_col"],
                "label": ch["label"],
                "description": ch["description"],
                "type": "cross_model_channel",
                "color": ch["color"],
                "dashed": True,
            }
        )

    return {
        "tables": tables,
        "edges": edges,
        "models": MODEL_METADATA,
    }


def render_interactive_markdown(
    schema_path: Path,
    js_src: str = "../javascripts/interactive_schema.js",
) -> str:
    """Generate Markdown page with embedded interactive canvas and LinkML-extracted data."""
    graph_data = extract_schema_graph(schema_path)
    data_json = json.dumps(graph_data)

    pop_mermaid = generate_mermaid_erd(schema_path, POPULATION_CLASSES)
    reg_mermaid = generate_mermaid_erd(schema_path, REGIONAL_CLASSES)

    # Indent Mermaid blocks by 4 spaces for MkDocs tab blocks
    pop_mermaid_indented = "\n".join(
        "    " + line if line.strip() else "" for line in pop_mermaid.splitlines()
    )
    reg_mermaid_indented = "\n".join(
        "    " + line if line.strip() else "" for line in reg_mermaid.splitlines()
    )

    return f"""# Database Schema & Entity-Relationship Diagrams

This page presents the compiled Entity-Relationship (ER) diagrams and foreign key contracts linking the multi-model population, vehicle fleet, land-use, and network skim tables across **UrbanSim**, **DEMOS**, **ATLAS**, **POLARIS**, and **OMX Skims** for Deliverable #1.

All tables, column definitions, primary keys, foreign keys, and cross-model handoff relationships are **generated directly from the LinkML schema contracts** (`src/synergy_schema/schema/deliverable_1_static_schema.yaml`).

---

## 1. Core Population & Vehicle Fleet ERD

The diagram below isolates the synthetic agent tables across DEMOS, ATLAS, and POLARIS with explicit relational cardinalities:

=== "Mermaid ER Diagram (Standard Crows-Feet)"

    ```mermaid
{pop_mermaid_indented}
    ```

=== "Graphviz Diagram (Attribute Ports)"

    <div class="erd-diagram-card">
      <p><a href="../assets/images/deliverable_1_population_erd.svg" target="_blank" class="md-button md-button--primary">Open High-Resolution Population ERD (Vector SVG)</a></p>
      <img src="../assets/images/deliverable_1_population_erd.svg" alt="Core Synthetic Population and Vehicle Fleet ER Diagram" class="erd-diagram-img" />
    </div>

---

## 2. Complete 5-Model Regional Architecture ERD

The regional architecture diagram links all 12 tables across the 5 models, including UrbanSim Census Block marginals, Block-to-TAZ aggregation tables, and Open Matrix (`.omx`) travel impedance matrices.

=== "Mermaid ER Diagram (Standard Crows-Feet)"

    ```mermaid
{reg_mermaid_indented}
    ```

=== "Graphviz Diagram (Attribute Ports)"

    <div class="erd-diagram-card">
      <p><a href="../assets/images/deliverable_1_erd.svg" target="_blank" class="md-button md-button--primary">Open High-Resolution Regional ERD (Vector SVG)</a></p>
      <img src="../assets/images/deliverable_1_erd.svg" alt="Complete 5-Model Regional Architecture ER Diagram" class="erd-diagram-img" />
    </div>

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

---

## 4. Interactive Schema Inspector

The interactive canvas below provides dynamic filtering and metadata inspection for individual tables and columns:

<div class="schema-explorer-outer">
  <!-- Controls Bar -->
  <div class="schema-explorer-toolbar">
    <div class="schema-filter-group">
      <span class="schema-toolbar-label">Model:</span>
      <button class="schema-filter-btn active" data-model="ALL">All Models</button>
      <button class="schema-filter-btn" data-model="UrbanSim">UrbanSim</button>

      <button class="schema-filter-btn" data-model="DEMOS">DEMOS</button>
      <button class="schema-filter-btn" data-model="ATLAS">ATLAS</button>
      <button class="schema-filter-btn" data-model="POLARIS">POLARIS</button>
      <button class="schema-filter-btn" data-model="Skims">OMX Skims</button>
    </div>
    <div class="schema-actions-group">
      <div class="schema-search-box">
        <input type="text" id="schema-search-input" placeholder="Search tables or columns..." />
      </div>
      <div class="schema-zoom-controls">
        <button id="schema-zoom-in" title="Zoom In">+</button>
        <button id="schema-zoom-out" title="Zoom Out">&minus;</button>
        <button id="schema-zoom-fit" title="Fit to View">Fit View</button>
        <button id="schema-fullscreen" title="Toggle Fullscreen">&#x26F6;</button>
      </div>
    </div>
  </div>

  <!-- Main Viewport -->
  <div id="schema-viewport" class="schema-viewport">
    <svg id="schema-svg-layer" class="schema-svg-layer"></svg>
    <div id="schema-nodes-layer" class="schema-nodes-layer"></div>

    <!-- Inspector Drawer -->
    <div id="schema-inspector" class="schema-inspector hidden">
      <div class="schema-inspector-header">
        <div class="schema-inspector-title-wrap">
          <span id="inspector-model-badge" class="schema-model-badge">MODEL</span>
          <h3 id="inspector-table-name">Table Name</h3>
        </div>
        <button id="inspector-close-btn" class="schema-close-btn">&times;</button>
      </div>
      <div class="schema-inspector-body">
        <p id="inspector-description" class="schema-inspector-desc"></p>

        <h4>Relationships</h4>
        <div id="inspector-relationships" class="schema-relationships-list"></div>

        <h4>Columns & Field Types</h4>
        <div id="inspector-columns-table-wrap">
          <table class="schema-columns-table">
            <thead>
              <tr>
                <th>Field</th>
                <th>Type</th>
                <th>Key / Crosswalk</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody id="inspector-columns-body"></tbody>
          </table>
        </div>
      </div>
    </div>
  </div>

  <!-- Legend -->
  <div class="schema-legend">
    <span class="legend-item"><span class="legend-line solid-line"></span> Solid Line: Within-Model Foreign Key</span>
    <span class="legend-item"><span class="legend-line dashed-line"></span> Dashed Line: Cross-Model Data Handoff Channel</span>
    <span class="legend-item"><span class="legend-badge pk-badge">PK</span> Primary Key</span>
    <span class="legend-item"><span class="legend-badge fk-badge">FK</span> Foreign Key</span>
    <span class="legend-item"><span class="legend-badge cw-badge">X-*</span> Categorical Crosswalk Rule</span>
  </div>
</div>

<script>
window.SCHEMA_GRAPH_DATA = {data_json};
</script>
<script src="{js_src}"></script>
"""


def generate_interactive_diagram(
    schema_path: Path | None = None,
    output_path: Path | None = None,
    js_src: str = "../javascripts/interactive_schema.js",
) -> Path:
    """Generate and write interactive schema documentation page."""
    base_dir = Path(__file__).resolve().parent.parent.parent
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
    content = render_interactive_markdown(schema_path, js_src=js_src)
    output_path.write_text(content, encoding="utf-8")
    return output_path


if __name__ == "__main__":
    out = generate_interactive_diagram()
    print(f"Generated interactive schema documentation page at {out}")
