# Population snapshots and artifact identity

A population snapshot describes households, people, vehicles, and declared
relationships at one simulation year. The records are occurrences in time, not
timeless master entities. Longitudinal references can connect occurrences
across years without assuming that every identifier or relationship persists.

The focused [population relationship
overview](../schema/core-schema-uml.md#population-relationship-overview) shows
household, person, and vehicle occurrences connected through explicit
membership and vehicle-assignment records. Co-location in a file is not treated
as proof of a relationship.

Artifact identity answers a different question: which exact file bytes carried
the records? A content digest stays stable when a file moves and changes when
its contents change. Provenance then records which workflow run produced or
consumed those bytes.

Separating population identity, artifact identity, and provenance prevents a
shared row identifier, a filename, or a run record from being asked to prove
more than it can.
