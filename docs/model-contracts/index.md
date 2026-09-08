# Model contract review

Use these pages to review one model's native record shapes without first
navigating the shared handoff, mapping, or workflow material. Each class link
opens the generated LinkML reference, including its field table, annotations,
relationships, and direct source declaration.

The pages distinguish established current-workflow projections from provisional
observed model contracts. A provisional contract is real review surface, but it
does not establish a shared release, mapping, or cross-model handoff.

| Model | Established review surface | Provisional observed surface |
| --- | --- | --- |
| [ATLAS](atlas.md) | Household and person inputs; vehicle output | Paired fleet-output CSV row shapes |
| [ActivitySim](activitysim.md) | Household, person, and land-use-zone identity projections | None currently |
| [UrbanSim](urbansim.md) | Household and person identity projections | None currently |
| [POLARIS](polaris.md) | Translated household, person, and vehicle projections | Selected demand-database population tables |
| [DEMOS](demos.md) | None currently | Mapped household and person CSV exports |

For review, first confirm whether the listed physical surface and direction are
correct. Then amend field descriptions, types, requiredness, identities,
vocabularies, and codebook references as supported by the producer. Keep
cross-model mappings and workflow-specific behavior outside the model page
until their owners approve them.
