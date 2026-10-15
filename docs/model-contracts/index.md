# Model contract review

These pages let a model team review how Synergy describes their tables,
without wading through the handoff, mapping, or workflow material first. Each
class link opens the generated reference page, with its fields, notes,
relationships, and source definition.

Each page separates two kinds of records. **Established** records are the ones
the current workflow already uses. **Provisional** records were sketched from
example files and still need the model team to confirm them. Provisional
records can be reviewed, but they don't yet count as a shared release, a
mapping, or a handoff between models.

| Model | Established records | Provisional observed rows |
| --- | --- | --- |
| [ATLAS](atlas.md) | Household and person inputs; vehicle output | Paired fleet-output CSV row shapes |
| [ActivitySim](activitysim.md) | Household, person, and land-use-zone identity and join records | None currently |
| [UrbanSim](urbansim.md) | Household and person identity and join records | None currently |
| [POLARIS](polaris.md) | Translated household, person, and vehicle records | Selected demand-database population tables |
| [DEMOS](demos.md) | None currently | Mapped household and person CSV exports |

When reviewing, first check that each listed table, export, or setting is
real and points the right way (input versus output). Then correct field
descriptions, types, required fields, IDs, allowed values, and codebook
references based on what the model actually produces. Leave cross-model
mappings and workflow-specific behavior off the model page until their owners
approve them.
