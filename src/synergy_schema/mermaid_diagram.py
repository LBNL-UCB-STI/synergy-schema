"""Generate Mermaid erDiagram specifications directly from LinkML schema."""

from __future__ import annotations

from pathlib import Path
import textwrap

from linkml_runtime.utils.schemaview import SchemaView

# Mapping of LinkML class names to clean display types for Mermaid ERD
POPULATION_CLASSES = [
    "DemosPolarisMappedHousehold",
    "DemosPolarisMappedPerson",
    "AtlasHouseholdFleetOutput",
    "AtlasVehicleFleetOutput",
    "PolarisDemandDatabaseHousehold",
    "PolarisDemandDatabasePerson",
    "PolarisDemandDatabaseVehicle",
]

REGIONAL_CLASSES = [
    "UrbanSimBlockMarginals",
    "BlockToTazMapping",
    "UrbanSimZonalTotals",
    "DemosPolarisMappedHousehold",
    "DemosPolarisMappedPerson",
    "AtlasHouseholdFleetOutput",
    "AtlasVehicleFleetOutput",
    "PolarisDemandDatabaseHousehold",
    "PolarisDemandDatabasePerson",
    "PolarisDemandDatabaseVehicle",
    "InputNetworkSkims",
    "NextYearNetworkSkims",
    "ActivitySimHouseholdInputRecord",
    "ActivitySimPersonInputRecord",
    "BeamHouseholdRecord",
    "BeamPersonRecord",
    "BeamVehicleRecord",
    "BeamPlanRecord",
    "BeamNetworkSkims",
]


def _clean_type(range_val: str | None) -> str:
    """Normalize LinkML range types to clean alphanumeric types for Mermaid."""
    if not range_val:
        return "string"
    mapping = {
        "integer": "int",
        "int": "int",
        "string": "string",
        "str": "string",
        "float": "float",
        "double": "float",
        "boolean": "bool",
        "bool": "bool",
    }
    return mapping.get(str(range_val).lower(), "string")


def _clean_comment(comment: str) -> str:
    """Escape comments for Mermaid ER diagram string literals."""
    return (
        comment.replace('"', "'")
        .replace("{", "")
        .replace("}", "")
        .replace("\n", " ")
        .strip()
    )


def generate_mermaid_erd(
    schema_path: Path,
    include_classes: list[str] | None = None,
    title: str = "Database ER Diagram",
) -> str:
    """Generate a Mermaid erDiagram string from the LinkML schema."""
    view = SchemaView(str(schema_path))
    target_classes = set(include_classes or REGIONAL_CLASSES)

    lines: list[str] = [
        "erDiagram",
    ]

    # 1. Define Relationships
    # Intra-model relationships
    if (
        "DemosPolarisMappedHousehold" in target_classes
        and "DemosPolarisMappedPerson" in target_classes
    ):
        lines.append(
            '    DemosPolarisMappedHousehold ||--|{ DemosPolarisMappedPerson : "contains"'
        )

    if (
        "AtlasHouseholdFleetOutput" in target_classes
        and "AtlasVehicleFleetOutput" in target_classes
    ):
        lines.append(
            '    AtlasHouseholdFleetOutput ||--|{ AtlasVehicleFleetOutput : "owns"'
        )

    if (
        "PolarisDemandDatabaseHousehold" in target_classes
        and "PolarisDemandDatabasePerson" in target_classes
    ):
        lines.append(
            '    PolarisDemandDatabaseHousehold ||--|{ PolarisDemandDatabasePerson : "contains"'
        )

    if (
        "PolarisDemandDatabaseHousehold" in target_classes
        and "PolarisDemandDatabaseVehicle" in target_classes
    ):
        lines.append(
            '    PolarisDemandDatabaseHousehold ||--|{ PolarisDemandDatabaseVehicle : "owns"'
        )

    if (
        "UrbanSimBlockMarginals" in target_classes
        and "BlockToTazMapping" in target_classes
    ):
        lines.append('    UrbanSimBlockMarginals ||--|{ BlockToTazMapping : "maps_to"')

    if (
        "UrbanSimZonalTotals" in target_classes
        and "BlockToTazMapping" in target_classes
    ):
        lines.append('    UrbanSimZonalTotals ||--|{ BlockToTazMapping : "aggregates"')

    # Cross-model handoffs
    if (
        "DemosPolarisMappedHousehold" in target_classes
        and "AtlasHouseholdFleetOutput" in target_classes
    ):
        lines.append(
            '    DemosPolarisMappedHousehold ||--|| AtlasHouseholdFleetOutput : "1:1 fleet join"'
        )

    if (
        "DemosPolarisMappedHousehold" in target_classes
        and "PolarisDemandDatabaseHousehold" in target_classes
    ):
        lines.append(
            '    DemosPolarisMappedHousehold ||--|| PolarisDemandDatabaseHousehold : "pop recode lineage"'
        )

    if (
        "AtlasVehicleFleetOutput" in target_classes
        and "PolarisDemandDatabaseVehicle" in target_classes
    ):
        lines.append(
            '    AtlasVehicleFleetOutput ||--|| PolarisDemandDatabaseVehicle : "vehicle recode"'
        )

    if (
        "UrbanSimBlockMarginals" in target_classes
        and "DemosPolarisMappedHousehold" in target_classes
    ):
        lines.append(
            '    UrbanSimBlockMarginals ||--o{ DemosPolarisMappedHousehold : "marginal control"'
        )

    if (
        "UrbanSimZonalTotals" in target_classes
        and "PolarisDemandDatabaseHousehold" in target_classes
    ):
        lines.append(
            '    UrbanSimZonalTotals ||--o{ PolarisDemandDatabaseHousehold : "TAZ location"'
        )

    if (
        "UrbanSimZonalTotals" in target_classes
        and "InputNetworkSkims" in target_classes
    ):
        lines.append(
            '    UrbanSimZonalTotals ||--o{ InputNetworkSkims : "TAZ dimension"'
        )

    if (
        "UrbanSimZonalTotals" in target_classes
        and "NextYearNetworkSkims" in target_classes
    ):
        lines.append(
            '    UrbanSimZonalTotals ||--o{ NextYearNetworkSkims : "TAZ dimension"'
        )

    # ActivitySim intra-model & cross-model
    if (
        "ActivitySimHouseholdInputRecord" in target_classes
        and "ActivitySimPersonInputRecord" in target_classes
    ):
        lines.append(
            '    ActivitySimHouseholdInputRecord ||--|{ ActivitySimPersonInputRecord : "contains"'
        )

    if (
        "DemosPolarisMappedHousehold" in target_classes
        and "ActivitySimHouseholdInputRecord" in target_classes
    ):
        lines.append(
            '    DemosPolarisMappedHousehold ||--|| ActivitySimHouseholdInputRecord : "pop lineage"'
        )

    if (
        "AtlasHouseholdFleetOutput" in target_classes
        and "ActivitySimHouseholdInputRecord" in target_classes
    ):
        lines.append(
            '    AtlasHouseholdFleetOutput ||--|| ActivitySimHouseholdInputRecord : "updates cars"'
        )

    if (
        "UrbanSimBlockMarginals" in target_classes
        and "ActivitySimHouseholdInputRecord" in target_classes
    ):
        lines.append(
            '    UrbanSimBlockMarginals ||--o{ ActivitySimHouseholdInputRecord : "block control"'
        )

    if (
        "UrbanSimZonalTotals" in target_classes
        and "ActivitySimHouseholdInputRecord" in target_classes
    ):
        lines.append(
            '    UrbanSimZonalTotals ||--o{ ActivitySimHouseholdInputRecord : "TAZ location"'
        )

    # BEAM intra-model & cross-model
    if "BeamHouseholdRecord" in target_classes and "BeamPersonRecord" in target_classes:
        lines.append('    BeamHouseholdRecord ||--|{ BeamPersonRecord : "contains"')

    if (
        "BeamHouseholdRecord" in target_classes
        and "BeamVehicleRecord" in target_classes
    ):
        lines.append('    BeamHouseholdRecord ||--|{ BeamVehicleRecord : "owns"')

    if "BeamPersonRecord" in target_classes and "BeamVehicleRecord" in target_classes:
        lines.append('    BeamPersonRecord ||--o{ BeamVehicleRecord : "drives"')

    if "BeamPersonRecord" in target_classes and "BeamPlanRecord" in target_classes:
        lines.append('    BeamPersonRecord ||--|{ BeamPlanRecord : "executes"')

    if (
        "DemosPolarisMappedHousehold" in target_classes
        and "BeamHouseholdRecord" in target_classes
    ):
        lines.append(
            '    DemosPolarisMappedHousehold ||--|| BeamHouseholdRecord : "pop lineage"'
        )

    if (
        "AtlasVehicleFleetOutput" in target_classes
        and "BeamVehicleRecord" in target_classes
    ):
        lines.append(
            '    AtlasVehicleFleetOutput ||--|| BeamVehicleRecord : "vehicle staging"'
        )

    if (
        "UrbanSimBlockMarginals" in target_classes
        and "BeamHouseholdRecord" in target_classes
    ):
        lines.append(
            '    UrbanSimBlockMarginals ||--o{ BeamHouseholdRecord : "block control"'
        )

    if (
        "UrbanSimZonalTotals" in target_classes
        and "BeamHouseholdRecord" in target_classes
    ):
        lines.append(
            '    UrbanSimZonalTotals ||--o{ BeamHouseholdRecord : "TAZ location"'
        )

    if "UrbanSimZonalTotals" in target_classes and "BeamNetworkSkims" in target_classes:
        lines.append(
            '    UrbanSimZonalTotals ||--o{ BeamNetworkSkims : "TAZ dimension"'
        )

    lines.append("")

    # 2. Define Entities with Attributes
    for cls_name in sorted(target_classes):
        cls_def = view.get_class(cls_name)
        if not cls_def:
            continue

        lines.append(f"    {cls_name} {{")
        induced_slots = view.class_induced_slots(cls_name)

        # Primary keys first, then foreign keys, then attributes
        pk_slots = []
        fk_slots = []
        other_slots = []

        for slot in induced_slots:
            is_pk = bool(slot.identifier or slot.key)
            is_fk = bool(slot.annotations and "foreign_key" in slot.annotations)

            # Manual PK/FK overrides based on contract knowledge if not annotated
            if cls_name == "DemosPolarisMappedHousehold" and slot.name == "household":
                is_pk = True
            elif cls_name == "DemosPolarisMappedPerson" and slot.name == "person":
                is_pk = True
            elif cls_name == "DemosPolarisMappedPerson" and slot.name == "household":
                is_fk = True
            elif cls_name == "AtlasHouseholdFleetOutput" and slot.name == "houseid":
                is_pk = True
            elif cls_name == "AtlasVehicleFleetOutput" and slot.name == "vehid":
                is_pk = True
            elif cls_name == "AtlasVehicleFleetOutput" and slot.name == "houseid":
                is_fk = True
            elif (
                cls_name == "PolarisDemandDatabaseHousehold"
                and slot.name == "household"
            ):
                is_pk = True
            elif (
                cls_name == "PolarisDemandDatabaseHousehold" and slot.name == "location"
            ):
                is_fk = True
            elif cls_name == "PolarisDemandDatabasePerson" and slot.name == "person":
                is_pk = True
            elif cls_name == "PolarisDemandDatabasePerson" and slot.name == "household":
                is_fk = True
            elif (
                cls_name == "PolarisDemandDatabaseVehicle" and slot.name == "vehicle_id"
            ):
                is_pk = True
            elif cls_name == "PolarisDemandDatabaseVehicle" and slot.name == "hhold":
                is_fk = True
            elif cls_name == "UrbanSimBlockMarginals" and slot.name == "block_id":
                is_pk = True
            elif cls_name == "UrbanSimZonalTotals" and slot.name == "zone_id":
                is_pk = True
            elif cls_name == "BlockToTazMapping" and slot.name in {
                "block_id",
                "zone_id",
            }:
                is_fk = True
            elif (
                cls_name in {"InputNetworkSkims", "NextYearNetworkSkims"}
                and slot.name == "file_path"
            ):
                is_pk = True
            elif (
                cls_name in {"InputNetworkSkims", "NextYearNetworkSkims"}
                and slot.name == "zone_count"
            ):
                is_fk = True
            elif (
                cls_name == "ActivitySimHouseholdInputRecord"
                and slot.name == "household_id"
            ):
                is_pk = True
            elif cls_name == "ActivitySimHouseholdInputRecord" and slot.name in {
                "TAZ",
                "taz",
                "block_id",
                "cars",
            }:
                is_fk = True
            elif (
                cls_name == "ActivitySimPersonInputRecord" and slot.name == "member_id"
            ):
                is_pk = True
            elif cls_name == "ActivitySimPersonInputRecord" and slot.name in {
                "household_id",
                "work_zone_id",
                "school_zone_id",
            }:
                is_fk = True
            elif cls_name == "BeamHouseholdRecord" and slot.name == "household_id":
                is_pk = True
            elif cls_name == "BeamHouseholdRecord" and slot.name in {
                "block_id",
                "home_zone_id",
            }:
                is_fk = True
            elif cls_name == "BeamPersonRecord" and slot.name == "person_id":
                is_pk = True
            elif cls_name == "BeamPersonRecord" and slot.name in {
                "household_id",
                "home_zone_id",
                "workplace_zone_id",
                "school_zone_id",
            }:
                is_fk = True
            elif cls_name == "BeamVehicleRecord" and slot.name == "vehicle_id":
                is_pk = True
            elif cls_name == "BeamVehicleRecord" and slot.name in {
                "household_id",
                "maindriver_id",
                "source_vehicle_id",
            }:
                is_fk = True
            elif cls_name == "BeamPlanRecord" and slot.name in {
                "person_id",
                "tour_id",
                "trip_id",
            }:
                is_fk = True
            elif cls_name == "BeamNetworkSkims" and slot.name == "file_path":
                is_pk = True
            elif cls_name == "BeamNetworkSkims" and slot.name == "zone_count":
                is_fk = True

            if is_pk:
                pk_slots.append(slot)
            elif is_fk:
                fk_slots.append(slot)
            else:
                other_slots.append(slot)

        for slot in pk_slots + fk_slots + other_slots:
            clean_t = _clean_type(slot.range)
            key_tag = ""
            if slot in pk_slots and slot in fk_slots:
                key_tag = "PK, FK"
            elif slot in pk_slots:
                key_tag = "PK"
            elif slot in fk_slots:
                key_tag = "FK"

            # Optional short description/comment
            desc = ""
            if slot.description:
                # First sentence only, max 40 chars without splitting words
                first_sent = slot.description.split(".")[0].strip()
                if len(first_sent) > 40:
                    first_sent = textwrap.shorten(
                        first_sent, width=40, placeholder="..."
                    )
                desc = f' "{_clean_comment(first_sent)}"'
            elif slot.annotations and "foreign_key" in slot.annotations:
                desc = (
                    f' "{_clean_comment(str(slot.annotations["foreign_key"].value))}"'
                )

            if key_tag:
                lines.append(f"        {clean_t} {slot.name} {key_tag}{desc}")
            else:
                lines.append(f"        {clean_t} {slot.name}{desc}")

        lines.append("    }")
        lines.append("")

    return "\n".join(lines)
