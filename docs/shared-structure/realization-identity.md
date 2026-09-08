# Population trajectory realization identity

This page is the public interoperability definition for
`synergy:scenario-realization:population-trajectory-v1`. It gives a selected
PILATES population trajectory one portable content identity. That identity
allows independent systems to determine whether they selected the same
scenario revision, realization, ordered snapshots, and member files even when
the surrounding manifests or storage locations differ.

The definition does not create a registry, a Tracker protocol, an artifact
locator policy, or runtime admission behavior. Those concerns sit outside the
identity being compared.

## Identity envelope

Every v1 identity has exactly these fields:

```yaml
kind: synergy:scenario-realization:population-trajectory-v1
projection_version: "1"
digest_algorithm: sha256
content_digest: <64 lowercase hexadecimal characters>
```

`content_digest` is SHA-256 over the canonical representation below. It is not
part of the bytes it hashes. `kind`, `projection_version`, and
`digest_algorithm` are part of those bytes, so a later canonical representation must use a
new kind or version rather than silently changing v1 rules.

`ScenarioRealizationIdentity` and `ScenarioRealizationReceipt` are published
in the provider-neutral LinkML schema at
[`src/synergy_schema/schema/core/handoff_bundle.yaml`](https://github.com/LBNL-UCB-STI/synergy-schema/blob/main/src/synergy_schema/schema/core/handoff_bundle.yaml).
The PILATES `PopulationTrajectoryBundle` profile composes them with the source
manifest fields.

## Closed v1 canonical representation

After validation, construct a new mapping with exactly this shape. Do not copy
the input bundle and delete selected fields; unrecognized source fields are
excluded unless a later `projection_version` explicitly adds them.

```yaml
kind: synergy:scenario-realization:population-trajectory-v1
projection_version: "1"
digest_algorithm: sha256
manifest_version: <root manifest version>
scenario_definition:
  scenario_definition_id: <id>
  revision: <revision>
  digest_algorithm: sha256
  content_digest: <scenario definition digest>
stochastic_realization_id: <id>
trajectory:
  trajectory_id: <id>
  requested_years: [<ascending unique integer years>]
  skipped_years: [<ascending unique integer years>]
  completeness_status: <complete or incomplete>
  membership_rule:
    profile: pilates-population-snapshot-v1
    required_roles: [households, persons, vehicles]
    optional_roles: []
  snapshots:
    - snapshot_id: <id>
      manifest_version: <snapshot bundle manifest version>
      simulation_year: <integer>
      equilibrium_iteration: <integer, when present>
      parent_snapshot_ref: <id, when present>
      completeness_status: <complete or incomplete>
      members:
        - semantic_role: <households, persons, or vehicles>
          artifact_identity:
            digest_algorithm: sha256
            content_digest: <member byte digest>
          schema_contract:
            language: <schema language>
            schema_digest_algorithm: sha256
            schema_digest: <schema source digest>
            selected_root: <schema root>
```

The canonical representation includes the declared scenario, realization, trajectory, and
snapshot context; requested/successful/skipped year closure; completeness;
member roles; selected artifact byte identities; and schema interpretation
identities. It excludes the outer exchange `id`, locators, storage paths,
schema URI and version labels, media observations, row counts, diagnostics,
timestamps, validation/admission/execution evidence, Consist or Tracker run
references, human annotations, receipts, and both digest-result fields.

## Required validation

Before returning a canonical representation or digest, a conforming implementation must:

1. validate the declared `PopulationTrajectoryBundle` LinkML shape;
2. validate cross-record scenario, trajectory, year, provenance, and artifact
   agreement required by the source envelope;
3. validate this profile's canonical-representation rules; and
4. compare any supplied top-level or receipt identity to the calculated
   identity.

Reject missing root or snapshot manifest versions; malformed SHA-256 digests;
missing member schema contracts; duplicate snapshot IDs; duplicate or missing
semantic roles within a snapshot; invalid `snapshot_id`/semantic-role member
selection; non-ascending or duplicate requested/skipped years; skipped years
outside the requested set or overlapping successful years; non-increasing
snapshot years; invalid/missing parent snapshots; inconsistent scenario or
stochastic-realization references; and inconsistent completeness. A successful
snapshot bundle must be complete. Invalid input receives no realization digest.

## Canonical bytes

Serialize the closed canonical representation as UTF-8 using the
[RFC 8785 JSON Canonicalization Scheme (JCS)](https://www.rfc-editor.org/rfc/rfc8785).
For this v1 profile, values are restricted to objects with string keys, arrays,
strings containing Unicode scalar values, integers, and booleans. `null`,
floating-point values, non-finite numbers, non-string object keys, Unicode
surrogates, and unsupported host-language values are invalid.

Integers must be in the interoperable range `-(2**53 - 1)` through
`2**53 - 1`, inclusive. Object keys use RFC 8785 UTF-16 code-unit ordering.
Snapshots stay in their validated increasing simulation-year order; members
are ordered by semantic role; requested/skipped years and required/optional
role lists are already required to be ascending. Omit absent optional fields;
an explicit `null` is invalid.

## Interoperability artifact and release pin

The repository commits a standalone v1 test vector:

- canonical UTF-8 JCS bytes:
  [`tests/fixtures/population_trajectory_v1.jcs.json`](https://github.com/LBNL-UCB-STI/synergy-schema/blob/main/tests/fixtures/population_trajectory_v1.jcs.json)
- expected SHA-256:
  [`tests/fixtures/population_trajectory_v1.sha256`](https://github.com/LBNL-UCB-STI/synergy-schema/blob/main/tests/fixtures/population_trajectory_v1.sha256)
  (`4651ff4cb5471f36c9632df1e3d3ec37a9ff81352cc2d1990cac6a3b2fd919b5`)
- structured identity/profile definition:
  [`handoff_bundle.yaml`](https://github.com/LBNL-UCB-STI/synergy-schema/blob/main/src/synergy_schema/schema/core/handoff_bundle.yaml)
  and
  [`pilates_population.yaml`](https://github.com/LBNL-UCB-STI/synergy-schema/blob/main/src/synergy_schema/schema/profiles/pilates_population.yaml)

A receiver should cite a released Synergy tag or commit containing these files,
then independently reproduce the published bytes and digest. A release tag is
the stable reference; a moving branch name is not.

## Trust boundary and receipts

Parsing an unpinned bundle only establishes self-consistency: the supplied
bundle produces the supplied realization identity. It does not authenticate a
publisher or prove that the sender delivered a previously selected realization.
A receiver that needs that assurance must compare against an independently supplied expected identity from trusted configuration, a reviewed Git release, or another independent channel.

`ScenarioRealizationReceipt` is separately versioned mutable evidence about a
realization. It may hold locations, observations, validation, admission, or
execution provenance, but those facts never enter the v1 digest. A receipt
identity must match the calculated realization identity. During migration a
receipt may be physically adjacent to the source bundle; it remains logically
outside this manifest's canonical representation. Consumers that do not need receipt evidence
may ignore it entirely.

## Compatibility

`manifest_content_digest` is retained only as a legacy logical full parsed
bundle digest. It changes when any included envelope evidence changes and is
neither original-document-byte integrity nor a realization or registry
identity. Future derived profiles, including POLARIS translations, require
their own published canonical representation and test vector before they can claim a
realization identity.
