# Scenario compatibility

Two models can participate in the same scenario without representing every
assumption in the same way. Compatibility records make the difference between
a supported assumption, a visible gap, an intentional override, and a true
conflict explicit.

| Situation | Recorded decision | Consequence |
| --- | --- | --- |
| No conflict | `compatible` | The native setting represents the shared assumption. |
| Gap | `compatible_with_gaps` with the unsupported assumption named | The model remains in the exchange, and the missing coverage stays visible. |
| Override | An intentional native value and rationale | The completed check is rejected until the difference is resolved or accepted under the study's rules. |
| Conflict | Incompatible authoritative declarations | The completed check is rejected and the scenario must be reconciled. |

A gap is not silently upgraded to agreement, and an override is not mislabeled
as compatibility. This makes the shared-universe claim precise without
requiring all participating models to have identical capabilities.
