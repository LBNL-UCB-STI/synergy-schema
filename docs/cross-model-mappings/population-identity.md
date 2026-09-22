# Population identity

Population identity answers which household, person, membership, or vehicle a
record represents. It is different from a row number, a file checksum, and a
state occurrence in one year.

Some native identifiers persist across models or years. Others are local
ordinals that are meaningful only inside one table or snapshot. Synergy records
that distinction explicitly so an accidental equality of integers is not
treated as proof that two rows describe the same entity.

For example, inside a single household's file, people may simply be numbered
`1`, `2`, and `3` (`member_id`). An accidental match where another household
also has a member `1` does not mean they are the same person. In contrast, a
longitudinal reference (such as `person:synthetic-evolving:alex`) persists across
years and simulation steps even as that individual changes households, ages, or
acquires a vehicle.

The generated [identity map](../schema/cross-model-population-identity.md) shows
which identifiers are preserved, renamed, derived, composite, or local at the
UrbanSim, ActivitySim, ATLAS, and POLARIS boundaries.
