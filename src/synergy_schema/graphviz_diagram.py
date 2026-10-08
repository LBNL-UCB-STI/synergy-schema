"""Generate high-resolution Graphviz ER diagrams directly from LinkML schema."""

from __future__ import annotations

import argparse
from pathlib import Path
import graphviz
from linkml_runtime.utils.schemaview import SchemaView


MODEL_CLUSTERS = {
    "UrbanSim": {
        "label": "UrbanSim (Land Use & Zonal Marginals)",
        "classes": [
            "UrbanSimBlockMarginals",
            "BlockToTazMapping",
            "UrbanSimZonalTotals",
        ],
        "header_bg": "#dbeafe",
        "header_fg": "#1e40af",
        "border_color": "#93c5fd",
        "cluster_bg": "#f8fafc",
    },
    "DEMOS": {
        "label": "DEMOS (Demographic Synthesis)",
        "classes": ["DemosPolarisMappedHousehold", "DemosPolarisMappedPerson"],
        "header_bg": "#f3e8ff",
        "header_fg": "#6b21a8",
        "border_color": "#d8b4fe",
        "cluster_bg": "#fdf4ff",
    },
    "ATLAS": {
        "label": "ATLAS (Household Fleet Synthesis)",
        "classes": ["AtlasHouseholdFleetOutput", "AtlasVehicleFleetOutput"],
        "header_bg": "#dcfce7",
        "header_fg": "#166534",
        "border_color": "#86efac",
        "cluster_bg": "#f0fdf4",
    },
    "POLARIS": {
        "label": "POLARIS (Activity-Based Demand Database)",
        "classes": [
            "PolarisDemandDatabaseHousehold",
            "PolarisDemandDatabasePerson",
            "PolarisDemandDatabaseVehicle",
        ],
        "header_bg": "#ffedd5",
        "header_fg": "#9a3412",
        "border_color": "#fdba74",
        "cluster_bg": "#fff7ed",
    },
    "Skims": {
        "label": "Network Travel Skims (Open Matrix .omx)",
        "classes": ["InputNetworkSkims", "NextYearNetworkSkims"],
        "header_bg": "#ccfbf1",
        "header_fg": "#115e59",
        "border_color": "#5eead4",
        "cluster_bg": "#f0fdfa",
    },
}

INTRA_MODEL_RELATIONSHIPS = [
    # (child_class, child_col, parent_class, parent_col, label)
    ("BlockToTazMapping", "block_id", "UrbanSimBlockMarginals", "block_id", "N:1"),
    ("BlockToTazMapping", "zone_id", "UrbanSimZonalTotals", "zone_id", "N:1"),
    (
        "DemosPolarisMappedPerson",
        "household",
        "DemosPolarisMappedHousehold",
        "household",
        "N:1",
    ),
    (
        "AtlasVehicleFleetOutput",
        "houseid",
        "AtlasHouseholdFleetOutput",
        "houseid",
        "N:1",
    ),
    (
        "PolarisDemandDatabasePerson",
        "household",
        "PolarisDemandDatabaseHousehold",
        "household",
        "N:1",
    ),
    (
        "PolarisDemandDatabaseVehicle",
        "hhold",
        "PolarisDemandDatabaseHousehold",
        "household",
        "N:1",
    ),
]

CROSS_MODEL_RELATIONSHIPS = [
    # (child_class, child_col, parent_class, parent_col, label, color)
    (
        "DemosPolarisMappedHousehold",
        "block_id",
        "UrbanSimBlockMarginals",
        "block_id",
        "Marginal Control (N:1)",
        "#0284c7",
    ),
    (
        "PolarisDemandDatabaseHousehold",
        "location",
        "UrbanSimZonalTotals",
        "zone_id",
        "TAZ Location (N:1)",
        "#ea580c",
    ),
    (
        "AtlasHouseholdFleetOutput",
        "houseid",
        "DemosPolarisMappedHousehold",
        "household",
        "1:1 Fleet Join",
        "#16a34a",
    ),
    (
        "InputNetworkSkims",
        "zone_count",
        "UrbanSimZonalTotals",
        "zone_id",
        "TAZ Dimension (N:1)",
        "#0d9488",
    ),
    (
        "NextYearNetworkSkims",
        "zone_count",
        "UrbanSimZonalTotals",
        "zone_id",
        "TAZ Dimension (N:1)",
        "#0d9488",
    ),
]


def _build_table_html(sv: SchemaView, cn: str, info: dict, cross_refs: list) -> str:
    rows = [
        f'<TR><TD BGCOLOR="{info["header_bg"]}" COLSPAN="2" BORDER="1" COLOR="{info["border_color"]}" ALIGN="CENTER">'
        f'<FONT COLOR="{info["header_fg"]}"><B>{cn}</B></FONT></TD></TR>'
    ]

    for sn in sv.class_slots(cn):
        s = sv.induced_slot(sn, cn)
        ann = s.annotations or {}
        fk = "foreign_key" in ann or any(r[0] == cn and r[1] == sn for r in cross_refs)
        pk = bool(s.identifier or s.key)

        if pk:
            key_tag = ' <FONT COLOR="#b45309"><B>[PK]</B></FONT>'
        elif fk:
            key_tag = ' <FONT COLOR="#2563eb"><I>[FK]</I></FONT>'
        else:
            key_tag = ""

        rng = s.range or "str"
        if len(rng) > 16:
            rng = rng[:14] + ".."

        rows.append(
            f"<TR>"
            f'<TD PORT="{sn}" BORDER="1" COLOR="#e2e8f0" ALIGN="LEFT">{sn}{key_tag}</TD>'
            f'<TD BORDER="1" COLOR="#e2e8f0" ALIGN="RIGHT"><FONT COLOR="#64748b">{rng}</FONT></TD>'
            f"</TR>"
        )

    return (
        '<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4" BGCOLOR="#ffffff">'
        + "".join(rows)
        + "</TABLE>>"
    )


def generate_graphviz_erd(
    schema_path: Path,
    output_base: Path,
    rankdir: str = "TB",
) -> Path:
    """Generate both SVG and PNG ER diagrams for the full 5-model static architecture."""
    sv = SchemaView(str(schema_path))

    dot = graphviz.Digraph("Deliverable1_ERD", format="svg")
    dot.attr(
        "graph",
        rankdir=rankdir,
        compound="true",
        nodesep="0.6",
        ranksep="1.0",
        bgcolor="transparent",
        fontname="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
        fontsize="13",
        splines="polyline",
    )
    dot.attr(
        "node",
        shape="none",
        fontname="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
        fontsize="10",
    )
    dot.attr(
        "edge",
        fontname="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
        fontsize="9",
        arrowsize="0.8",
    )

    for model_name, info in MODEL_CLUSTERS.items():
        with dot.subgraph(name=f"cluster_{model_name}") as sub:
            sub.attr(
                label=info["label"],
                fontname="Helvetica-Bold",
                fontsize="12",
                fontcolor=info["header_fg"],
                style="rounded,filled",
                fillcolor=info["cluster_bg"],
                color=info["border_color"],
                penwidth="1.5",
            )

            for cn in info["classes"]:
                cls = sv.get_class(cn)
                if not cls:
                    continue
                sub.node(
                    cn, label=_build_table_html(sv, cn, info, CROSS_MODEL_RELATIONSHIPS)
                )

    # Add intra-model foreign keys
    for src_c, src_p, tgt_c, tgt_p, lbl in INTRA_MODEL_RELATIONSHIPS:
        dot.edge(
            f"{src_c}:{src_p}",
            f"{tgt_c}:{tgt_p}",
            label=f" {lbl} ",
            color="#2563eb",
            penwidth="1.8",
            dir="forward",
        )

    # Add cross-model pipeline joins
    for src_c, src_p, tgt_c, tgt_p, lbl, col in CROSS_MODEL_RELATIONSHIPS:
        dot.edge(
            f"{src_c}:{src_p}",
            f"{tgt_c}:{tgt_p}",
            label=f" {lbl} ",
            color=col,
            style="dashed",
            penwidth="1.6",
            dir="forward",
        )

    output_base.parent.mkdir(parents=True, exist_ok=True)
    svg_out = dot.render(str(output_base), format="svg", cleanup=True)
    dot.render(str(output_base), format="png", cleanup=True)

    return Path(svg_out)


def generate_population_erd(
    schema_path: Path,
    output_base: Path,
    rankdir: str = "LR",
) -> Path:
    """Generate focused SVG and PNG ER diagrams for synthetic population & vehicle fleet tables."""
    sv = SchemaView(str(schema_path))

    pop_clusters = {
        "DEMOS": MODEL_CLUSTERS["DEMOS"],
        "ATLAS": MODEL_CLUSTERS["ATLAS"],
        "POLARIS": MODEL_CLUSTERS["POLARIS"],
    }

    pop_intra = [
        (
            "DemosPolarisMappedPerson",
            "household",
            "DemosPolarisMappedHousehold",
            "household",
            "N:1",
        ),
        (
            "AtlasVehicleFleetOutput",
            "houseid",
            "AtlasHouseholdFleetOutput",
            "houseid",
            "N:1",
        ),
        (
            "PolarisDemandDatabasePerson",
            "household",
            "PolarisDemandDatabaseHousehold",
            "household",
            "N:1",
        ),
        (
            "PolarisDemandDatabaseVehicle",
            "hhold",
            "PolarisDemandDatabaseHousehold",
            "household",
            "N:1",
        ),
    ]

    pop_cross = [
        (
            "AtlasHouseholdFleetOutput",
            "houseid",
            "DemosPolarisMappedHousehold",
            "household",
            "1:1 Fleet Join",
            "#16a34a",
        ),
        (
            "PolarisDemandDatabaseHousehold",
            "household",
            "DemosPolarisMappedHousehold",
            "household",
            "Pop Recode Lineage",
            "#9333ea",
        ),
        (
            "PolarisDemandDatabaseVehicle",
            "vehicle_id",
            "AtlasVehicleFleetOutput",
            "vehid",
            "Fleet Vehicle Recode",
            "#0284c7",
        ),
    ]

    dot = graphviz.Digraph("Deliverable1_Population_ERD", format="svg")
    dot.attr(
        "graph",
        rankdir=rankdir,
        compound="true",
        nodesep="0.6",
        ranksep="1.1",
        bgcolor="transparent",
        fontname="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
        fontsize="13",
        splines="polyline",
    )
    dot.attr(
        "node",
        shape="none",
        fontname="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
        fontsize="10",
    )
    dot.attr(
        "edge",
        fontname="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
        fontsize="9",
        arrowsize="0.8",
    )

    for model_name, info in pop_clusters.items():
        with dot.subgraph(name=f"cluster_{model_name}") as sub:
            sub.attr(
                label=info["label"],
                fontname="Helvetica-Bold",
                fontsize="12",
                fontcolor=info["header_fg"],
                style="rounded,filled",
                fillcolor=info["cluster_bg"],
                color=info["border_color"],
                penwidth="1.5",
            )

            for cn in info["classes"]:
                cls = sv.get_class(cn)
                if not cls:
                    continue
                sub.node(cn, label=_build_table_html(sv, cn, info, pop_cross))

    for src_c, src_p, tgt_c, tgt_p, lbl in pop_intra:
        dot.edge(
            f"{src_c}:{src_p}",
            f"{tgt_c}:{tgt_p}",
            label=f" {lbl} ",
            color="#2563eb",
            penwidth="1.8",
            dir="forward",
        )

    for src_c, src_p, tgt_c, tgt_p, lbl, col in pop_cross:
        dot.edge(
            f"{src_c}:{src_p}",
            f"{tgt_c}:{tgt_p}",
            label=f" {lbl} ",
            color=col,
            style="dashed",
            penwidth="1.6",
            dir="forward",
        )

    output_base.parent.mkdir(parents=True, exist_ok=True)
    svg_out = dot.render(str(output_base), format="svg", cleanup=True)
    dot.render(str(output_base), format="png", cleanup=True)

    return Path(svg_out)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate Graphviz ER diagrams from LinkML schema."
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path("src/synergy_schema/schema/deliverable_1_static_schema.yaml"),
        help="Path to Deliverable 1 root schema YAML.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs/assets/images"),
        help="Directory to store rendered diagrams.",
    )
    args = parser.parse_args()

    full_base = args.output_dir / "deliverable_1_erd"
    pop_base = args.output_dir / "deliverable_1_population_erd"

    svg_full = generate_graphviz_erd(args.schema, full_base, rankdir="TB")
    svg_pop = generate_population_erd(args.schema, pop_base, rankdir="LR")

    print(f"Rendered Full Architecture ERD to: {svg_full}")
    print(f"Rendered Focused Population ERD to: {svg_pop}")


if __name__ == "__main__":
    main()
