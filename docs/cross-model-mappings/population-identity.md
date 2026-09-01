# Population identity

Population identity answers which household, person, membership, or vehicle a
record represents. It is different from a row number, a file checksum, and a
state occurrence in one year.

Some native identifiers persist across models or years. Others are local
ordinals that are meaningful only inside one table or snapshot. Synergy records
that distinction explicitly so an accidental equality of integers is not
treated as proof that two rows describe the same entity.

The generated [identity map](../schema/cross-model-population-identity.md) shows
which identifiers are preserved, renamed, derived, composite, or local at the
UrbanSim, ActivitySim, ATLAS, and POLARIS boundaries.
