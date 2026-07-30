---
search:
  boost: 5.0
---

# Slot: artifacts 


_Artifact references carried by this provenance handoff._



<div data-search-exclude markdown="1">



URI: [https://w3id.org/consist/binding/artifacts](https://w3id.org/consist/binding/artifacts)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [ConsistProvenanceDocument](ConsistProvenanceDocument.md) | A portable provenance handoff with one enclosing ledger context and graph fac... |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [ConsistArtifactReference](ConsistArtifactReference.md) |
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


* from schema: https://w3id.org/consist/binding




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | https://w3id.org/consist/binding/artifacts |
| native | https://w3id.org/consist/binding/artifacts |




## LinkML Source

<details>
```yaml
name: artifacts
description: Artifact references carried by this provenance handoff.
from_schema: https://w3id.org/consist/binding
rank: 1000
owner: ConsistProvenanceDocument
domain_of:
- ConsistProvenanceDocument
range: ConsistArtifactReference
multivalued: true
inlined: true
inlined_as_list: true

```
</details></div>