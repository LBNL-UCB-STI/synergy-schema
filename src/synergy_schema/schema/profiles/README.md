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

The first workflow profile is `pilates_population.yaml`. It composes a
post-ATLAS yearly `PopulationSnapshotBundle` from a population snapshot and
households, persons, and vehicles artifact members, then documents each role's
ATLAS-owned native contract root. The native row definitions remain in
`../models/atlas/`; this profile does not copy their fields. The bundle also
requires a `ConsistProvenanceDocument` from the pinned module under
`../vendor/`. This operational provenance stays in the PILATES profile rather
than leaking into shared population concepts or ATLAS-owned rows.

## Identity-bearing population projections

The current population slice also documents the small, identity-bearing
projections that PILATES connects across UrbanSim, ActivitySim, ATLAS, and
POLARIS. These are not full native-table definitions. They expose only the
fields needed to describe identity, household membership, and the current
location joins; the model-owned schemas and the typed mapping manifest retain
the physical spellings and the observed PILATES evidence.

`household_id` and `person_id` are preserved where the mapping declares an
entity identifier or household-membership relationship. Local ordinals are a
different kind of value: ActivitySim can regenerate `member_id` after person
filtering, and the ATLAS-to-POLARIS translation derives POLARIS's zero-based
`id`. A matching number therefore does not by itself establish a durable
person identity.

Zones remain model-specific relationships. For example, the ActivitySim
projection explicitly records its `taz` relationship and its current work and
school zone aliases; it does not declare a universal zone domain or perform a
geographic lookup. Similarly, `vehicle_id` is preserved only as an
artifact-scoped POLARIS vehicle identifier, not as a cross-artifact vehicle
identity.

LinkML validates the declared shape of each projection: required fields,
types, and the named relationship targets. The focused tests add checks for
the synthetic mapping path and its recorded evidence, but neither layer opens
model artifacts nor proves cross-artifact referential integrity, full
population coverage, or runtime enforcement. Those remain separate
model-owner and workflow-validation work.
