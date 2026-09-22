# Design rationale

Synergy separates shared facts, model-owned interfaces, mapping decisions, and
run evidence because they have different owners and change at different rates.
Combining them would make a convenient file today but leave future changes hard
to interpret: a new column, a changed assumption, and a new executable would
all look like the same kind of revision.

These notes explain the main design choices and their costs. They also describe
the cases where flat files and a README already provide enough coordination.

## Common questions

**Why not share one wide population table?** Different models own different
facts and update them at different times. The shared structure identifies the
facts that must agree without turning one model's table into everyone else's
runtime interface.

**Why use LinkML?** It keeps the definitions readable while supporting a
generated reference and structural validation.

**When are flat files enough?** A small, stable exchange with a clear owner may
need only files and a README. More structure earns its cost when versions,
mapping rules, ownership, and run evidence must remain comparable over time.

- [Why LinkML](why-linkml.md) explains the choice of a readable schema source.
- [Why not one big table?](why-not-one-big-table.md) explains the ownership and
  time boundaries behind the separate records.
- [Are flat files enough?](are-flat-files-enough.md) gives the threshold for
  adding more structure.
