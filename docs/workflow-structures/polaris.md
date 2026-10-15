# POLARIS translated population

## Current

POLARIS native records are partial in this schema. They're enough for a
synthetic translation example and some targeted checks, not full coverage of
the model.

The current schema defines the full `PolarisDemandDatabaseV1` contract (households,
persons, and vehicles) and links it to `mappings/releases/atlas-demos-to-polaris/revision-1/`.
The projection is implemented via DuckDB SQL transformations (`translation.sql`)
verified by SHA-256 byte hashes in `polaris-translation.yaml`.

## Proposed

A translation receipt would record the five yearly file roles, the source
population ledger, the reviewed one-year mapping, the registered translation
code, and any known scenario gaps. With those links, a checker can confirm the
translation used the right scenario and year.

## Out of scope

POLARIS runtime adapter enforcement is future work. This repository doesn't
claim a deployed POLARIS integration, automatic receipts, or sign-off from the
POLARIS team.
