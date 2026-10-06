# Population identity

Population identity is about which household, person, household membership,
or vehicle a record describes. That's different from a row number, a file
checksum, or a record describing someone in one particular year.

Some model IDs stay the same across models or years. Others are just row
numbers that only mean something inside one table or one year. Synergy records
which is which, so two rows that happen to share the number 42 aren't treated
as the same household.

The [contract review](../schema/contract-at-a-glance.md)
and [core schema UML](../schema/core-schema-uml.md)
show how canonical identities, memberships, and translation contracts connect
native model views to core entity tables.
