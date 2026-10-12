"""Tests for SynthFirm model LinkML schemas."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest
from linkml.validator import Validator
from linkml.validator.plugins import JsonschemaValidationPlugin
from linkml_runtime.utils.schemaview import SchemaView

REPO_ROOT = Path(__file__).parents[1]
SYNTHFIRM_SCHEMA_PATH = (
    REPO_ROOT
    / "src"
    / "synergy_schema"
    / "schema"
    / "models"
    / "synthfirm"
    / "synthfirm.yaml"
)
EVIDENCE_DIR = REPO_ROOT / "evidence" / "synthfirm_SF_baseline011226"


def test_synthfirm_schema_structure() -> None:
    view = SchemaView(str(SYNTHFIRM_SCHEMA_PATH))
    assert view.schema.name == "synthfirm"
    assert "SynthFirm" in view.schema.description

    classes = set(view.all_classes())
    assert "SynthFirmEstablishmentRecord" in classes
    assert "SynthFirmCarrierRecord" in classes
    assert "SynthFirmB2BShipmentRecord" in classes
    assert "SynthFirmInternationalFreightRecord" in classes

    # Test SynthFirmEstablishmentRecord
    estab = view.induced_class("SynthFirmEstablishmentRecord")
    assert estab.attributes["BusID"].identifier is True
    assert estab.attributes["BusID"].required is True
    assert estab.attributes["fleet_id"].required is True
    assert estab.attributes["Industry_NAICS6_Make"].required is True
    assert estab.attributes["Emp"].minimum_value == 0.0
    assert "synthetic_firms_with_fleet_mc_adjusted" in estab.aliases

    # Test SynthFirmCarrierRecord
    carrier = view.induced_class("SynthFirmCarrierRecord")
    assert carrier.is_a == "SynthFirmEstablishmentRecord"
    assert "SCTG1" in carrier.attributes
    assert "SCTG5" in carrier.attributes
    assert carrier.attributes["SCTG1"].minimum_value == 0
    assert carrier.attributes["SCTG1"].maximum_value == 1

    # Test SynthFirmB2BShipmentRecord
    shipment = view.induced_class("SynthFirmB2BShipmentRecord")
    assert shipment.attributes["shipment_id"].identifier is True
    assert shipment.attributes["BuyerID"].annotations["foreign_key"].value == (
        "SynthFirmEstablishmentRecord.BusID"
    )
    assert shipment.attributes["SellerID"].annotations["foreign_key"].value == (
        "SynthFirmEstablishmentRecord.BusID"
    )
    assert shipment.attributes["TruckLoad"].minimum_value == 0.0

    # Test SynthFirmInternationalFreightRecord
    intl = view.induced_class("SynthFirmInternationalFreightRecord")
    assert intl.attributes["bundle_id"].identifier is True
    assert intl.attributes["PORTID"].required is True
    assert intl.attributes["is_airport"].required is True


def test_synthfirm_enums() -> None:
    view = SchemaView(str(SYNTHFIRM_SCHEMA_PATH))
    enums = set(view.all_enums())
    assert "SynthFirmModeChoiceEnum" in enums
    assert "SynthFirmPowertrainEnum" in enums
    assert "SynthFirmPortTypeEnum" in enums

    mode_enum = view.get_enum("SynthFirmModeChoiceEnum")
    assert "For-hire Truck" in mode_enum.permissible_values
    assert "Private Truck" in mode_enum.permissible_values

    powertrain_enum = view.get_enum("SynthFirmPowertrainEnum")
    assert "Battery Electric" in powertrain_enum.permissible_values
    assert "H2 Fuel Cell" in powertrain_enum.permissible_values
    assert "PHEV" in powertrain_enum.permissible_values


def test_synthfirm_validator_instances() -> None:
    validator = Validator(
        SYNTHFIRM_SCHEMA_PATH,
        validation_plugins=[JsonschemaValidationPlugin(closed=False)],
    )

    valid_establishment = {
        "BusID": 408228,
        "fleet_id": 1,
        "CBPZONE": 9,
        "FAFZONE": 61,
        "esizecat": 1,
        "Industry_NAICS6_Make": "424200",
        "Commodity_SCTG": 21,
        "Emp": 6.95,
        "MESOZONE": "20009",
        "lat": 35.1743,
        "lon": -115.3325,
        "state_abbr": "CA",
        "EV_powertrain": "Battery Electric",
        "diesel_class_4_6": 1.0,
        "n_trucks": 1.0,
    }
    report = validator.validate(valid_establishment, "SynthFirmEstablishmentRecord")
    assert len(report.results) == 0

    valid_carrier = {
        **valid_establishment,
        "BusID": 5726,
        "Industry_NAICS6_Make": "484000",
        "SCTG1": 1,
        "SCTG2": 0,
        "SCTG3": 1,
        "SCTG4": 1,
        "SCTG5": 1,
    }
    report_carrier = validator.validate(valid_carrier, "SynthFirmCarrierRecord")
    assert len(report_carrier.results) == 0

    valid_shipment = {
        "shipment_id": 101,
        "BuyerID": 408228,
        "BuyerZone": "20009",
        "BuyerNAICS": "424200",
        "SellerID": 5726,
        "SellerZone": "20001",
        "SellerNAICS": "484000",
        "TruckLoad": 15.5,
        "Commodity_SCTG": 21,
        "SCTG_Group": 2,
        "UnitCost": 125.0,
        "orig_FAFID": 61,
        "dest_FAFID": 64,
        "mode_choice": "For-hire Truck",
        "probability": 0.85,
        "Distance": 42.5,
        "Travel_time": 55.0,
    }
    report_shipment = validator.validate(valid_shipment, "SynthFirmB2BShipmentRecord")
    assert len(report_shipment.results) == 0

    # Negative validation test: negative employment
    invalid_establishment = {
        **valid_establishment,
        "Emp": -5.0,
    }
    report_invalid = validator.validate(
        invalid_establishment, "SynthFirmEstablishmentRecord"
    )
    assert len(report_invalid.results) > 0


@pytest.mark.skipif(
    not EVIDENCE_DIR.exists(),
    reason="SynthFirm evidence directory not available in local workspace",
)
def test_synthfirm_validates_against_real_evidence_sample() -> None:
    validator = Validator(
        SYNTHFIRM_SCHEMA_PATH,
        validation_plugins=[JsonschemaValidationPlugin(closed=False)],
    )

    # 1. Test sample row from synthetic_firms_with_fleet_mc_adjusted.csv
    firms_csv = (
        EVIDENCE_DIR
        / "firm_and_fleet"
        / "2018"
        / "synthetic_firms_with_fleet_mc_adjusted.csv"
    )
    if firms_csv.exists():
        with open(firms_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            row = next(reader)
            payload = {
                "BusID": int(row["BusID"]),
                "fleet_id": int(row["fleet_id"]),
                "CBPZONE": int(row["CBPZONE"]),
                "FAFZONE": int(row["FAFZONE"]),
                "esizecat": int(row["esizecat"]),
                "Industry_NAICS6_Make": str(row["Industry_NAICS6_Make"]),
                "Commodity_SCTG": int(row["Commodity_SCTG"]),
                "Emp": float(row["Emp"]),
                "MESOZONE": str(row["MESOZONE"]),
                "lat": float(row["lat"]),
                "lon": float(row["lon"]),
                "state_abbr": str(row["state_abbr"]),
                "EV_powertrain": str(row["EV_powertrain (if any)"])
                if row.get("EV_powertrain (if any)")
                else "None",
                "n_trucks": float(row["n_trucks"]),
            }
            report = validator.validate(payload, "SynthFirmEstablishmentRecord")
            assert len(report.results) == 0

    # 2. Test sample row from synthetic_carriers.csv
    carriers_csv = EVIDENCE_DIR / "firm_and_fleet" / "2018" / "synthetic_carriers.csv"
    if carriers_csv.exists():
        with open(carriers_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            row = next(reader)
            payload = {
                "BusID": int(row["BusID"]),
                "fleet_id": int(row["fleet_id"]),
                "CBPZONE": int(row["CBPZONE"]),
                "FAFZONE": int(row["FAFZONE"]),
                "esizecat": int(row["esizecat"]),
                "Industry_NAICS6_Make": str(row["Industry_NAICS6_Make"]),
                "Commodity_SCTG": int(row["Commodity_SCTG"]),
                "Emp": float(row["Emp"]),
                "MESOZONE": str(row["MESOZONE"]),
                "lat": float(row["lat"]),
                "lon": float(row["lon"]),
                "state_abbr": str(row["state_abbr"]),
                "EV_powertrain": str(row["EV_powertrain (if any)"])
                if row.get("EV_powertrain (if any)")
                else "None",
                "n_trucks": float(row["n_trucks"]),
                "SCTG1": int(row["SCTG1"]),
                "SCTG2": int(row["SCTG2"]),
                "SCTG3": int(row["SCTG3"]),
                "SCTG4": int(row["SCTG4"]),
                "SCTG5": int(row["SCTG5"]),
            }
            report = validator.validate(payload, "SynthFirmCarrierRecord")
            assert len(report.results) == 0

    # 3. Test sample row from import_OD_with_buyer.csv
    import_csv = (
        EVIDENCE_DIR / "B2B_Flow" / "International" / "import_OD_with_buyer.csv"
    )
    if import_csv.exists():
        with open(import_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            row = next(reader)
            payload = {
                "bundle_id": int(row["bundle_id"]),
                "flow_type": "import",
                "PORTID": int(row["PORTID"]),
                "port_location": str(row["CBP Port Location"]),
                "FAF": int(row["FAF"]),
                "CBPZONE": int(row["CBPZONE"]),
                "PORTZONE": str(row["PORTZONE"]),
                "port_type": str(row["TYPE"]),
                "is_airport": int(row["is_airport"]),
                "CFS_CODE": str(row["CFS_CODE"]),
                "CFS_NAME": str(row["CFS_NAME"]),
                "Commodity_SCTG": int(row["Commodity_SCTG"]),
                "SCTG_Group": int(row["SCTG_Group"]),
                "TruckLoad": float(row["TruckLoad"]),
                "mode_choice": str(row["mode_choice"]),
                "shipments": int(row["shipments"]),
                "Distance": float(row["Distance"]),
                "tmiles": float(row["tmiles"]),
                "BuyerID": int(row["BuyerID"]),
                "BuyerZone": str(row["BuyerZone"]),
                "BuyerNAICS": str(row["BuyerNAICS"]),
            }
            report = validator.validate(payload, "SynthFirmInternationalFreightRecord")
            assert len(report.results) == 0
