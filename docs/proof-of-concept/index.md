# A population that changes over three years

Two modeling workflows can use the same scenario name and year and still be
modeling different worlds. A household might split in one workflow but not the
other. A person might get a new ID between years. A policy might reach one
model through a setting while another model quietly ignores it. Comparing the
final results won't reveal which of these caused the difference.

Synergy Schema gives the models a shared way to describe the parts of the world
that need to match. This synthetic example follows one small population through
2025, 2030, and 2035:

- a new person joins,
- one household splits into two, and
- a vehicle moves with one of the new households.

There are two scenario branches, baseline and ZEV. Both start from the same
people and vehicles, but POLARIS assigns a different vehicle type in each. The
models can differ in the results they own while still describing the same
shared universe.

The example records scenario identity, how the population changes, the model
interfaces, mappings, reviews, and run/file evidence. It keeps shared IDs
separate from model-owned attributes, so workflows can produce different
results without silently describing different populations.

This tests the documented exchange format and the checks that compare files
against each other. It is not a deployed PILATES or POLARIS runtime, and it
doesn't show that a full regional population is valid. [Following the proof
from claim to file](check-the-showcase.md) walks through the records, the
evidence, the current review status, and two deliberately broken examples.
