# Design rationale

Synergy keeps shared facts, model interfaces, mapping decisions, and run
evidence in separate records because different people own them and they change
at different speeds. Lumping them together would make a convenient file today,
but later it would be hard to tell whether a change was a new column, a new
assumption, or a new version of the code.

These notes explain the main design choices and what they cost. They also say
when flat files and a README are enough.

## Common questions

**Why not share one wide population table?** Different models own different
facts and update them at different times. The shared structure pins down the
facts that must match, without turning one model's table into everyone else's
interface.

**Why use LinkML?** It keeps the definitions readable while also generating a
reference site and structural validation.

**When are flat files enough?** A small, stable exchange with a clear owner may
only need files and a README. More structure pays off when versions, mapping
rules, ownership, and run evidence need to stay comparable over time.

- [Why LinkML](why-linkml.md) explains the choice of schema language.
- [Why not one big table?](why-not-one-big-table.md) explains why the records
  are split up.
- [Are flat files enough?](are-flat-files-enough.md) covers when to add more
  structure.
