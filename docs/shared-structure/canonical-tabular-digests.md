# Canonical tabular content digests

A canonical tabular digest is a format-independent, deterministic cryptographic
identifier (`sha256:<64 hex>`) for the logical content of a table. It is
specified under the version tag `canonical_tabular_digest/v1`.

In Synergy's population ledger architecture, models write outputs and read inputs
in diverse physical formats: Parquet files, SQLite database tables, or CSVs.
Different write processes may emit different Parquet file metadata, compression
codecs, row chunking, or physical row orderings for the exact same underlying
data. Computing a standard file-byte SHA-256 hash across such files would report
spurious changes and break cache reuse.

`canonical_tabular_digest/v1` defines normalization and canonical serialization
rules that guarantee:
1. **Format independence**: The same logical data represented in Parquet, SQLite,
   or an in-memory table yields an identical content digest.
2. **Order invariance**: Writing rows in arbitrary physical order yields an
   identical content digest.
3. **Type precision**: Data types and null sentinels are normalized consistently
   so numbers, booleans, strings, and missing values are uniquely identified.

---

## 1. Normalization rules

### 1.1 Column ordering

Columns are ordered explicitly according to an authoritative schema specification:
- For **core attribute facets** (`core_facet_table/v1`), column order is
  determined by the LinkML attribute order defined on the corresponding core
  table class in `schema/core/core_tables.yaml`.
- For **model view tables** (`view_table/v1`), column order is determined by
  the table's native schema contract or physical DDL column definition.

Columns present in physical files but not declared in the schema are excluded.
Columns declared required by the schema but absent from physical data trigger
conformance failure.

### 1.2 Row sorting

Rows are deterministically ordered in ascending order by their primary key /
unique identifier columns:
- If a table has a single key column (e.g. `household_id` or `person_id`), rows
  are sorted ascending by that key.
- If a table has a composite key (e.g. `household_id`, `vehicle_id`), rows are
  sorted lexicographically by the key columns in declared order.
- Core table primary keys must be non-null.

### 1.3 Scalar type normalization

Every cell value is coerced and canonicalized:
- **Integers**: Represented as decimal integer strings without leading zeros
  (except the value `0`).
- **Floats**: IEEE 754 64-bit double precision floating point numbers:
  - `-0.0` is normalized to `+0.0`.
  - `NaN` is normalized to the string `nan`.
  - Finite floating point numbers are formatted with standard shortest decimal
    representation preserving round-trip IEEE 754 precision.
- **Strings**: Unicode strings normalized to NFC form, UTF-8 encoded.
- **Booleans**: Normalized to `true` or `false`.
- **Nulls**: Distinctly represented by the canonical token `\x00` (null byte
  sentinel) so that null is never confused with an empty string or zero.

### 1.4 Canonical row stream encoding

Each normalized row is encoded as a stream of UTF-8 bytes:
- Row values are formatted as a sequence of field byte slices delimited by an
  ASCII Unit Separator (`\x1f`).
- Each row terminates with an ASCII Record Separator (`\x1e`).
- The stream begins with a canonical header naming the profile, version, and
  ordered column names separated by `\x1f` and terminated by `\x1e`.

```
canonical_tabular_digest/v1\x1f<col1>\x1f<col2>\x1f...\x1e
<row1_val1>\x1f<row1_val2>\x1f...\x1e
<row2_val1>\x1f<row2_val2>\x1f...\x1e
```

### 1.5 Digest generation

The content digest is computed as the SHA-256 hash of the entire canonical row
stream, expressed as a lowercase hex string prefixed by `sha256:`:

$$\text{digest} = \text{"sha256:"} + \text{hex}(\text{SHA-256}(\text{row\_stream}))$$

---

## 2. Concrete profiles

### 2.1 `core_facet_table/v1`

Used for core attribute facet tables stored as Parquet files in the population
ledger (`stored_object` in `CoreFacetEntry`).
- **Target schema**: LinkML classes in `schema/core/core_tables.yaml`.
- **Primary key columns**:
  - `CoreHousehold`, `CoreHouseholdLocation`, `CoreHouseholdDwelling`: `[household_id]`
  - `CorePerson`, `CorePersonDemographics`, `CorePersonSchooling`, `CorePersonEmployment`: `[person_id]`
  - `CoreHouseholdMembership`: `[person_id]`
  - `CoreVehicle`: `[household_id, vehicle_id]`
- **Storage format**: Apache Parquet.

### 2.2 `view_table/v1`

Used for model view tables, including SQLite demand database tables
(`Demand.sqlite`) and model input/output views.
- **Target schema**: Model view schema contracts (e.g. `PolarisDemandDatabaseV1Household`,
  `PolarisDemandDatabaseV1Person`, `PolarisDemandDatabaseV1Vehicle`).
- **Primary key columns**: Table primary key columns defined in SQLite DDL or LinkML
  identifier slots.
- **Storage format**: SQLite tables, CSV files, or DuckDB relations.

### 2.3 `core_state/v1` (Merkle tree state digest)

Used for composite snapshot state trees (`state.state_digest` in `CoreState`).
It seals all established attribute facets into a single cryptographic digest:

1. Facet entries are sorted lexicographically by their facet name (e.g. `dwelling`,
   `employment`, `location`, `people`, `vehicles`).
2. Each facet contributes a line formatted as `<facet_name>:<facet_content_digest>\n`.
3. The Merkle root is computed as the SHA-256 hash of the concatenated lines,
   prefixed by `sha256:`.

$$\text{state\_digest} = \text{"sha256:"} + \text{hex}\left(\text{SHA-256}\left(\sum_{f \in \text{sorted facets}} f + \text{":"} + \text{digest}_f + \text{"\n"}\right)\right)$$

Any modification to any row in any facet table changes that facet's content digest,
which deterministically changes the snapshot's state digest.
