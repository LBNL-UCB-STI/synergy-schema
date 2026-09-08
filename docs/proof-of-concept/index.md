# A population that changes over three years

Two modeling workflows can use the same scenario name and simulation year yet
still describe different worlds. A household may split in one workflow but not
the other. A person may lose a stable identity between years. A policy may
reach one model through a configuration value while another model silently
ignores it. Comparing the final indicators does not reveal which of these
differences caused the result.

Synergy Schema provides a shared language for the parts of the world that need
to agree. This synthetic proof follows one small population through 2025, 2030,
and 2035. One person enters, one household becomes two, and one vehicle moves
with a successor household. Baseline and ZEV branches begin with the same
population identities while POLARIS retains a branch-specific vehicle type.
The models can therefore differ in what they own without losing the same shared
universe.

The proof records scenario identity, population change, model interfaces,
mappings, reviews, and run/file evidence. It keeps shared identities separate
from model-owned attributes, so workflows can differ without silently
describing different populations.

This is a test of the documented exchange shape and cross-file checks. It is
not a deployed PILATES or POLARIS runtime, and it does not establish that a
full regional population is valid. [Following the proof from claim to
file](check-the-showcase.md) presents the records, the evidence trail, the
current review status, and two deliberately broken exchanges.
