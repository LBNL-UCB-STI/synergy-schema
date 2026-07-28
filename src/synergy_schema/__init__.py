"""synergy-schema.

Shared POLARIS / BEAM CORE schemas for the Synergy project
"""

try:
    from synergy_schema._version import __version__, __version_tuple__
except ImportError:  # pragma: no cover
    __version__ = "0.0.0"
    __version_tuple__ = (0, 0, 0)
