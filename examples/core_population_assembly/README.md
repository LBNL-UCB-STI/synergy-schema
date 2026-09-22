# Core population assembly example

This synthetic example is the smallest staged assembly described in the
2026-09-21 core-population proposal. It describes one `2030` snapshot for
`synthetic-region` and two immutable contributions:

* DEMOS supplies households, people, and household membership.
* ATLAS adds vehicles and household--vehicle assignments.

The DEMOS household table also contains `will_move_next_iteration`. That
column is explicitly classified as a `model_view`; it is associated with the
same household state but does not assert a new core population fact.

`assembly.yaml` is a complete-for-named-consumer declaration for the synthetic
`vehicle-fleet-consumer-v1` requirements. Its resolved facet index makes the
selected authority explicit for every supplied core facet. The artifact
digests and schema-contract digests are synthetic values, included to make
identity checks deterministic; no external model run or Parquet exchange is
claimed.

The two `invalid-*.yaml` files are intentional checker fixtures:

* `invalid-overlapping-assertions.yaml` has DEMOS and ATLAS both assert the
  same core household `income` field without a field resolution.
* `invalid-missing-carried-through-upstream.yaml` marks a copied
  `household_id` as `carried_through` but does not name the upstream asserted
  field.

These fixtures test that authority cannot be inferred from contribution order
or from a matching native column name.
