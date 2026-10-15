# Scenario compatibility

Two models can take part in the same scenario without handling every
assumption the same way. Compatibility records spell out whether each
assumption is supported, missing, deliberately overridden, or in real
conflict.

| Situation | Recorded decision | Consequence |
| --- | --- | --- |
| No conflict | `compatible` | The model setting represents the shared assumption. |
| Gap | `compatible_with_gaps`, naming the unsupported assumption | The model stays in the exchange, and the missing piece stays visible. |
| Override | A deliberate model value, with a reason | The final check fails until the difference is fixed or accepted under the study's rules. |
| Conflict | Authoritative declarations that disagree | The final check fails and the scenario has to be reconciled. |

A gap never quietly turns into agreement, and an override is never labeled as
compatible. That keeps the "same shared universe" claim honest without
requiring every model to support every assumption.
