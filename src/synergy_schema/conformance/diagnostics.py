"""Deterministic result primitives shared by all conformance commands."""

from __future__ import annotations

from dataclasses import dataclass


class InputError(ValueError):
    """A malformed conformance invocation or document."""


@dataclass(frozen=True, order=True)
class Diagnostic:
    code: str
    message: str
    severity: str


@dataclass(frozen=True)
class CheckResult:
    diagnostics: tuple[Diagnostic, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "diagnostics", tuple(sorted(self.diagnostics)))

    @property
    def exit_code(self) -> int:
        return 1 if any(item.severity == "error" for item in self.diagnostics) else 0
