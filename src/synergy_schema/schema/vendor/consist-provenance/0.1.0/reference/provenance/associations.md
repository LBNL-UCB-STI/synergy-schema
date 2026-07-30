---
search:
  boost: 5.0
---

# Slot: associations 


_Consumption and production graph edges carried by this handoff._



<div data-search-exclude markdown="1">



URI: [https://w3id.org/consist/provenance/associations](https://w3id.org/consist/provenance/associations)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [ConsistProvenanceDocument](ConsistProvenanceDocument.md) | A portable provenance handoff with one enclosing ledger context and graph fac... |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [ConsistRunArtifactAssociation](ConsistRunArtifactAssociation.md) |
| Domain Of | [ConsistProvenanceDocument](ConsistProvenanceDocument.md) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |
| Multivalued | Yes |
### Slot Characteristics

| Property | Value |
| --- | --- |
| Owner | [ConsistProvenanceDocument](ConsistProvenanceDocument.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/consist/provenance




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | https://w3id.org/consist/provenance/associations |
| native | https://w3id.org/consist/provenance/associations |




## LinkML Source

<details>
```yaml
name: associations
description: Consumption and production graph edges carried by this handoff.
from_schema: https://w3id.org/consist/provenance
rank: 1000
owner: ConsistProvenanceDocument
domain_of:
- ConsistProvenanceDocument
range: ConsistRunArtifactAssociation
multivalued: true
inlined: true
inlined_as_list: true

```
</details></div>