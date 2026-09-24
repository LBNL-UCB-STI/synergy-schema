# Bring an existing mapping

Most model-to-model exchanges already have a spreadsheet, SQL query, script, or
column list behind them, often carrying years of hard-won knowledge. Synergy
starts from that material. Model teams don't have to redesign working files or
adopt a new runtime.

The goal is a small pilot around one representative year that can be undone
if it isn't worth it. The existing mapping becomes a versioned description
that people can read, review, and compare against the code and files used in a
real exchange.

## A three-step pilot

1. **[Inventory the file](day-zero-manifest.md).** Record one representative
   input or output, where it came from, and its fingerprint. The file itself
   doesn't change.
2. **[Write down the mapping](contract-at-a-glance.md).** Copy the existing
   spreadsheet, SQL, or script into rules people can review, including
   defaults, dropped fields, and other exceptions.
3. **[Run the one-year check](one-year-mapping-handshake.md).** Connect the
   reviewed rules to the code and files from one real exchange.

[Costs and exit](costs-and-exit.md) covers when this extra structure isn't
worth it, and how to back out.

## Inputs

The pilot needs one representative file, where it came from, the people who
own each side, and any historical incidents the exchange should guard against.
If nobody has an incident to report, none is made up.

The owners of each model still decide what their fields mean and whether the
cross-model mapping is acceptable. Synergy records their decisions in a
structured form and checks them; writing a mapping down in Synergy doesn't
transfer ownership. The [ownership
table](../shared-structure/glossary.md#ownership-and-authority) lays out who
decides what.

## What stays unchanged

Neither model has to change its runtime, rename fields, switch file formats,
or approve a schema just by taking part. The original mapping source stays
linked alongside the Synergy version.

## First useful result

Start with one export from the producing model and one named consumer. Keep
the file, record its checksum and the producer's version, and describe what
the consumer needs: IDs, join keys, units, year, and any defaults or dropped
information.

Run the consumer's existing import or dry-run path. Note whether it accepted
the file and whether the values still meant what they were supposed to.
Translation and validation at runtime stay with the consuming workflow.

For repeated exchanges or material mapping changes, the
[one-year mapping handshake](one-year-mapping-handshake.md) adds versioned
rules, links to the code, and review records. Track how long the first pilot
takes before estimating the cost of later ones.
