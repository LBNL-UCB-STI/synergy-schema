# Synergy Schema

A transportation modeling workflow can exchange perfectly readable files and
still leave a basic question unanswered: did every model represent the same
scenario, population, and point in time? Synergy Schema supplies a shared
language for answering that question across independently maintained systems.

## The coordination problem

Integrated studies often connect land-use, travel-demand, vehicle, and
traffic-simulation models. In this environment:

- **UrbanSim** models land use, real estate developments, and regional demographics;
- **ActivitySim** models daily activity schedules, tours, and travel demand;
- **ATLAS** models household vehicle fleet evolution, vehicle retirement, and EV technology adoption;
- **POLARIS** models agent-based traffic simulation, network assignments, and dynamic travel behavior; and
- **PILATES** serves as an orchestration pipeline coordinating these models across simulated years.

Each system has its own settings, tables, identifiers, release cycle, and
technical owners. A policy called `zev_mandate` in one model might appear as a
database value in another. A household identifier (such as `HH_100`) may
persist across years in one file, split into two households in another, or
identify only a row index in another. A path may still exist after its contents
have changed.

Ordinary file exchange does not settle questions such as:

- Which exact scenario assumptions were represented?
- Which population realization (random seed or simulation run) and simulation year does a file describe?
- Which identities persist across models or years, and which are local row IDs?
- Which mapping rules and executable code produced the translated rows?
- Which model owners reviewed those rules?
- Which exact input and output bytes were used in one run?

When those answers live only in filenames, meeting notes, or memory, two
workflows can appear aligned while quietly describing different worlds.

## One shared universe, several modeling systems

Synergy treats a study as one shared universe with several model-specific
views. Agreement concerns the facts that must be common: the scenario revision,
stochastic realization (the specific random seed or simulation run), simulation
year, population identity, declared relationships, and identity of exchanged
files. The PILATES modeling pipeline and POLARIS, along with ATLAS and other
systems, can keep their own schemas, settings, and model-specific results.

Different predictions are therefore not automatically conflicts. The systems
may legitimately produce different model-specific results. A conflict exists
when authoritative records disagree about a fact that the workflows explicitly
share. A model may also record a visible gap when it cannot represent one
shared assumption.

## Why the difficult records matter

Each record resolves a distinct coordination risk.

| Record | What it represents | Why it exists |
| --- | --- | --- |
| Interface descriptions | Model settings and table columns | Locate a shared idea in a model-owned setting, artifact key, or table column without taking ownership of that model's schema. |
| Mapping descriptions | Translation rules and known differences | Record how source values become target values, including defaults, lookups, filtered rows, and information that cannot be carried forward (mapping residue). |
| Review records | Model-owner decisions | Preserve the decision made by a person or team acting in a named authority role for one exact version of the rules. General agreement in a meeting is not enough when the mapping later changes. |
| Implementation links | Translation code and scripts | Identify the SQL or code that claims to apply the reviewed rules. Meaning and executable behavior can change independently. |
| Receipts and evidence | Verified execution records | Connect one scenario and year to the run, implementation, inputs, and outputs actually used. Evidence supports a bounded claim about an exchange; it does not prove that a model is scientifically correct. |
| Content digests | Cryptographic fingerprints | Give changing definitions and files stable fingerprints (hashes), allowing checks to distinguish an edited file from a moved or renamed one. |

Together they let the checker test declared consistency; evidence from the
producing and consuming runtimes is still required to establish actual use.

## Scope and limits

Synergy does not create one universal population table, rename native fields,
or require model-specific predictions to agree. It records the narrow shared
facts needed for coordination and leaves model-owned detail with the model that
produces or consumes it.

The current POLARIS material describes a proposed and tested exchange boundary,
not a completed POLARIS runtime integration. Public guides distinguish current,
proposed, and out-of-scope behavior where that boundary matters.

## How the documentation builds

The documentation forms a progression, while each section remains useful on
its own.

| Documentation area | Question it answers |
| --- | --- |
| [Model contract review](model-contracts/index.md) | What native tables, inputs, and outputs do ATLAS, ActivitySim, UrbanSim, POLARIS, and DEMOS expect or provide? |
| [Bring an existing mapping](bring-an-existing-mapping/index.md) | How can an existing spreadsheet, SQL script, or column mapping become a durable, reviewable exchange description? |
| [Three-year proof](proof-of-concept/index.md) | What do those distinctions look like in a small, executable example? |
| [Shared structure](shared-structure/index.md) | Which facts belong to the shared universe, and which remain model-owned? |
| [Cross-model mappings](cross-model-mappings/index.md) | How do identities, assumptions, and fields connect across models? |
| [Workflow structures](workflow-structures/index.md) | How are shared definitions combined at the PILATES and proposed POLARIS boundaries? |
| [Design rationale](design-rationale/index.md) | Why are the definitions separated this way, and when is a simpler approach enough? |
| [Glossary](shared-structure/glossary.md) | What do the recurring formal terms mean in plain language? |
| [Generated schema reference](schema/index.md) | What are the exact fields, types, required values, and relationships? |

The generated reference is the precise field-level source. The maintained
guides explain the problem, the boundaries, and the reasons those fields exist.
