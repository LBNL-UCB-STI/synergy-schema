# Model contract review

Use these pages to review one model's native record shapes without first
navigating the shared handoff, mapping, or workflow material. Each class link
opens the generated LinkML reference, including its field table, annotations,
relationships, and direct source declaration.

The pages distinguish established current-workflow record sets from provisional
observed model contracts. A provisional contract is reviewable, but it
does not establish a shared release, mapping, or cross-model handoff.

| Model | Established records | Provisional observed rows |
| --- | --- | --- |
| [ATLAS](atlas.md) | Household and person inputs; vehicle output | Paired fleet-output CSV row shapes |
| [ActivitySim](activitysim.md) | Household, person, and land-use-zone identity and join records | None currently |
| [UrbanSim](urbansim.md) | Household and person identity and join records | None currently |
| [POLARIS](polaris.md) | Translated household, person, and vehicle records | Selected demand-database population tables |
| [DEMOS](demos.md) | None currently | Mapped household and person CSV exports |

For review, first confirm whether the listed table, export, or configuration
item and its direction are correct. Then amend field descriptions, types, requiredness, identities,
vocabularies, and codebook references as supported by the producer. Keep
cross-model mappings and workflow-specific behavior outside the model page
until their owners approve them.
