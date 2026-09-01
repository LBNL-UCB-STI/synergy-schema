# Design rationale

Synergy separates shared facts, model-owned interfaces, mapping decisions, and
run evidence because they have different owners and change at different rates.
Combining them would make a convenient file today but leave future changes hard
to interpret: a new column, a changed assumption, and a new executable would
all look like the same kind of revision.

These notes explain the main design choices and their costs. They also describe
the cases where flat files and a README already provide enough coordination.

- [Why LinkML](why-linkml.md) explains the choice of a readable schema source.
- [Why not one big table?](why-not-one-big-table.md) explains the ownership and
  time boundaries behind the separate records.
- [Are flat files enough?](are-flat-files-enough.md) gives the threshold for
  adding more structure.
