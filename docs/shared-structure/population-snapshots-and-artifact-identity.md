# Population snapshots and artifact identity

A population snapshot describes the households, people, vehicles, and their
relationships in one simulation year. Each record describes something at one
point in time, not a permanent master entity. Longitudinal references can link
records across years, but nothing assumes every ID or relationship carries
over.

The [population relationship
overview](../schema/core-schema-uml.md#population-relationship-overview) shows
how households, people, and vehicles connect through explicit membership and
vehicle-assignment records. Two rows sitting in the same file are not taken as
proof that they're related.

Artifact identity answers a different question: which exact file carried the
records? A content digest stays the same when a file moves and changes when
its contents change. Provenance then records which run produced or used that
file.

Keeping population identity, file identity, and provenance separate means no
single row ID, filename, or run record is asked to prove more than it can.

Sometimes different models fill in different parts of the same snapshot at
different times. A
[core-population assembly](../workflow-structures/core-population-assembly.md)
lists those contributions, which never change once published, and builds an
index of which contribution supplies each part. It tells a consumer where the
authoritative data for each part lives. It doesn't merge the models' tables
or mean that a receiving model has accepted them.
