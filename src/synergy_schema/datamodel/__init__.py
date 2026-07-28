"""Data model package for synergy-schema."""

from pathlib import Path
from .synergy_schema import *  # noqa: F403

THIS_PATH = Path(__file__).parent

SCHEMA_DIRECTORY = THIS_PATH.parent / "schema"
MAIN_SCHEMA_PATH = SCHEMA_DIRECTORY / "synergy_schema.yaml"
