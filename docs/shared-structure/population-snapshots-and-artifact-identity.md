# Population snapshots and artifact identity

Snapshot-scoped household and person states describe who and what relationships
exist at a time. Artifact identity names exact delivered bytes. Provenance says
which workflow run produced those bytes. These are deliberately different
questions.

The focused [population relationship
overview](../schema/core-schema-uml.md#population-relationship-overview) shows
how household, person, and vehicle state occurrences connect through explicit
membership and vehicle-assignment records. Those relationship records prevent
the documentation from inferring household membership merely because person
and household rows happen to appear in the same snapshot.
