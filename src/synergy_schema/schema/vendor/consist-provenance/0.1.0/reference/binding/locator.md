---
search:
  boost: 5.0
---

# Slot: locator 


_An optional mutable hint for locating the ledger. It is never part of identity, equality, deduplication, or namespace assignment._



<div data-search-exclude markdown="1">



URI: [https://w3id.org/consist/binding/locator](https://w3id.org/consist/binding/locator)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [ConsistProvenanceContext](ConsistProvenanceContext.md) | The ledger context for portable Consist references |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [string](string.md) |
| Domain Of | [ConsistProvenanceContext](ConsistProvenanceContext.md) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |
### Slot Characteristics

| Property | Value |
| --- | --- |
| Owner | [ConsistProvenanceContext](ConsistProvenanceContext.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/consist/binding




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | https://w3id.org/consist/binding/locator |
| native | https://w3id.org/consist/binding/locator |




## LinkML Source

<details>
```yaml
name: locator
description: An optional mutable hint for locating the ledger. It is never part of
  identity, equality, deduplication, or namespace assignment.
from_schema: https://w3id.org/consist/binding
rank: 1000
owner: ConsistProvenanceContext
domain_of:
- ConsistProvenanceContext
range: string

```
</details></div>