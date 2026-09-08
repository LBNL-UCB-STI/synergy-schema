# Workflow profiles

A workflow profile describes the data a particular workflow actually expects
to read, write, or validate. It brings together definitions from the shared
and model-owned parts of the schema without copying them.

PILATES will be the first supported profile. Its profile will identify the
model schemas used at each workflow boundary, any transformed datasets that
PILATES owns, and the validation rules PILATES enforces.

A profile is about practical use, not ownership. Native BEAM or POLARIS
definitions still belong in [`../models/`](../models/), even when PILATES uses
them.

`pilates_population.yaml` composes a post-ATLAS yearly
`PopulationSnapshotBundle` from a snapshot plus household, person, and vehicle
artifacts, and names each ATLAS-owned contract root. Native rows remain in
`../models/atlas/`; this profile adds no fields. Its required vendored
`ConsistProvenanceDocument` stays operational, not shared or ATLAS-owned.

## Identity-bearing population records

The population slice records only the identity and join fields that PILATES
connects across UrbanSim, ActivitySim, ATLAS, and POLARIS. It is not a
native-table definition: model schemas and the mapping manifest retain physical
spellings and observed PILATES evidence.

`household_id` and `person_id` are preserved where the mapping declares an
entity identifier or household-membership relationship. Local ordinals are a
different kind of value: ActivitySim can regenerate `member_id` after person
filtering, and the ATLAS-to-POLARIS translation derives POLARIS's zero-based
`id`. A matching number therefore does not by itself establish a durable
person identity.

Zones remain model-specific relationships. For example, the ActivitySim
record set explicitly records its `taz` relationship and its current work and
school zone aliases; it does not declare a universal zone domain or perform a
geographic lookup. Similarly, ATLAS vehicle identity includes household,
vehicle, and forecast/output year, while the POLARIS row carries only `hhold`
and `vehicle_id`. The pair is meaningful only through the enclosing
`PopulationSnapshot` artifact and its matching `simulation_year`; `vehicle_id`
is not a cross-artifact vehicle identity.

LinkML validates the declared row shape of each record set: required fields
and types. The schema declares named relationship-target labels as annotations,
and the focused tests check those labels along with the synthetic mapping path
and its recorded evidence. Neither layer opens model artifacts nor proves
cross-artifact referential integrity, full population coverage, or runtime
enforcement. Those remain separate model-owner and workflow-validation work.
