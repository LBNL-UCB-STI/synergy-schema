# Population trajectory realization identity

This page is the public specification for
`synergy:scenario-realization:population-trajectory-v1`. It defines a single
fingerprint for a PILATES population trajectory. Two independent systems can
compare fingerprints to tell whether they picked the same scenario version,
random draw, sequence of yearly snapshots, and member files, even if their
manifests or storage locations differ.

This page only defines how to compute and compare that fingerprint. It does
not define a registry, a Tracker protocol, rules for where files live, or what
a runtime should accept.

## Identity envelope

Every v1 identity has exactly these fields:

```yaml
kind: synergy:scenario-realization:population-trajectory-v1
projection_version: "1"
digest_algorithm: sha256
content_digest: <64 lowercase hexadecimal characters>
```

`content_digest` is the SHA-256 hash of the canonical representation
described below. The digest itself is not part of what gets hashed, but
`kind`, `projection_version`, and `digest_algorithm` are. Any future change to
the canonical representation therefore needs a new kind or version; v1 rules
never change in place.

`ScenarioRealizationIdentity` and `ScenarioRealizationReceipt` are defined
in the shared LinkML schema at
[`src/synergy_schema/schema/core/handoff_bundle.yaml`](https://github.com/LBNL-UCB-STI/synergy-schema/blob/main/src/synergy_schema/schema/core/handoff_bundle.yaml).
The PILATES `PopulationTrajectoryBundle` profile combines them with the
source manifest fields.

## Closed v1 canonical representation

After validation, build a new object with exactly this shape. Don't copy the
input bundle and delete fields from it. Any field not listed here is left out,
unless a later `projection_version` explicitly adds it.

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

**Included:** the scenario, realization, trajectory, and snapshot context;
which years were requested, completed, and skipped; completeness; member
roles; the file fingerprints; and the fingerprints of the schemas used to
read them.

**Excluded:** the outer exchange `id`, locators and storage paths, schema URI
and version labels, media observations, row counts, diagnostics, timestamps,
validation/admission/execution evidence, Consist or Tracker run references,
human annotations, receipts, and both digest-result fields.

## Required validation

Before returning a canonical representation or digest, an implementation
must:

1. validate the declared `PopulationTrajectoryBundle` LinkML shape;
2. validate cross-record scenario, trajectory, year, provenance, and artifact
   agreement required by the source envelope;
3. validate this profile's canonical-representation rules; and
4. compare any supplied top-level or receipt identity to the calculated
   identity.

Reject the input if any of these are true:

- a root or snapshot manifest version is missing;
- a SHA-256 digest is malformed;
- a member has no schema contract;
- two snapshots share an ID;
- a snapshot has a duplicate or missing semantic role;
- a member selection by `snapshot_id` and semantic role is invalid;
- requested or skipped years are duplicated or not in ascending order;
- a skipped year is outside the requested set or also appears as a successful
  year;
- snapshot years don't strictly increase;
- a parent snapshot is invalid or missing;
- scenario or stochastic-realization references don't agree; or
- completeness is inconsistent.

A successful snapshot bundle must be complete. Invalid input gets no
realization digest.

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

A receiver should cite a released Synergy tag or commit that contains these
files, then reproduce the published bytes and digest on its own. Pin to a
release tag or commit, not a branch name, since branches move.

## Trust boundary and receipts

Computing the identity of a bundle on its own only shows that the bundle is
self-consistent: it produces the identity it claims. That doesn't prove who
published it, or that the sender delivered the realization the receiver
actually wanted. A receiver that needs that assurance must compare against an
independently supplied expected identity, such as one from trusted
configuration, a reviewed Git release, or another separate channel.

`ScenarioRealizationReceipt` is a separately versioned record that can be
updated over time. It can hold file locations, observations, and validation,
admission, or execution provenance, but none of that ever goes into the v1
digest. The identity on a receipt must match the calculated realization
identity. During migration a receipt may sit next to the source bundle, but it
is still outside the canonical representation. Consumers that don't need
receipt evidence can ignore it.

## Compatibility

`manifest_content_digest` is kept only for backward compatibility. It hashes
the whole parsed bundle, so it changes whenever any evidence in the bundle
changes. It is not a checksum of the original file bytes, and it is not a
realization or registry identity. Other profiles built on this one, including
POLARIS translations, need their own published canonical representation and
test vector before they can claim a realization identity.
