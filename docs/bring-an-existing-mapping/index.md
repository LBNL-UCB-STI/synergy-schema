# Bring an existing mapping

Many exchanges already have a spreadsheet, SQL query, script, or column table
that carries years of practical knowledge. Synergy begins with that material
instead of asking model teams to redesign working payloads or adopt a new
runtime.

The goal is a small, reversible pilot around one representative year. The
existing mapping becomes a versioned description that can be read, reviewed,
and compared with the code and files used in an actual exchange.

## Inputs

The pilot needs one representative payload, its producer context, named owners,
and any known historical incidents that the exchange should avoid. No incident
is invented when none has been supplied.

The named owners remain the decision authorities for native field meanings and
for accepting the cross-model mapping. Synergy records their work in a typed
form and checks it; transcription does not transfer ownership. The [ownership
table](../shared-structure/glossary.md#ownership-and-authority) makes the roles
explicit.

## What stays unchanged

Neither model must change its runtime, rename native fields, replace payload
formats, or approve a schema by implication. The original mapping source stays
identifiable alongside the Synergy representation.

## Outputs

The pilot produces a day-zero manifest, a one-year mapping review, and a
generated one-page mapping summary. Together they identify the existing files,
state the mapping rules and known losses, connect those rules to executable
code, and preserve review decisions.

## Typical timing

Discovery can begin as soon as the representative inputs are available. The
encode-and-return target is five business days after the inputs and owner
feedback arrive.
