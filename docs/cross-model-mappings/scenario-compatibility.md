# Scenario compatibility

Use explicit compatibility decisions rather than silently changing assumptions.

| Situation | Decision |
| --- | --- |
| No conflict | Bind the same value as `compatible`. |
| Gap | Record `compatible_with_gaps` and a named unsupported assumption. |
| Override | Reject the completed check until the rationale is resolved. |
| Conflict | Reject the completed check and reconcile the scenario. |
