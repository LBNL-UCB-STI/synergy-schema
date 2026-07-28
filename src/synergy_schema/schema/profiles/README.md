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
households, persons, and vehicles artifact members; native row definitions
remain model-owned and out of this profile.
