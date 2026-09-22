# Model contract review

Use these pages to review one model's native table and record structures without
first navigating the shared handoff, mapping, or workflow material. Each class link
opens the generated LinkML reference, including its field table, annotations,
relationships, and direct source declaration.

The pages distinguish two levels of maturity:

- **Established current-workflow records:** Native schema shapes actively
  integrated into the documented PILATES simulation pipeline.
- **Provisional observed model contracts:** Sample tables or exports observed from
  model teams. They are documented to support review and future integration, but
  do not establish a shared release, mapping, or pipeline handoff.

| Model | Domain role in pipeline | Established records | Provisional observed rows |
| --- | --- | --- | --- |
| [ATLAS](atlas.md) | Vehicle fleet evolution and EV adoption | Household and person inputs; vehicle output | Paired fleet-output CSV row shapes |
| [ActivitySim](activitysim.md) | Activity-based travel demand and schedules | Household, person, and land-use-zone identity and join records | None currently |
| [UrbanSim](urbansim.md) | Land use, parcel development, and location choice | Household and person identity and join records | None currently |
| [POLARIS](polaris.md) | Agent-based dynamic traffic and network simulation | Translated household, person, and vehicle records | Selected demand-database population tables |
| [DEMOS](demos.md) | Demographic synthesis and household evolution | None currently | Mapped household and person CSV exports |

For review, first confirm whether the listed table, export, or configuration
item and its direction are correct. Then amend field descriptions, types, requiredness, identities,
vocabularies, and codebook references as supported by the producer. Keep
cross-model mappings and workflow-specific behavior outside the model page
until their owners approve them.
