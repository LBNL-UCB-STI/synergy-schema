---
search:
  boost: 5.0
---

# Slot: artifact_id 


_The public Consist Artifact.id UUID._



<div data-search-exclude markdown="1">



URI: [https://w3id.org/consist/provenance/artifact_id](https://w3id.org/consist/provenance/artifact_id)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [ConsistArtifactReference](ConsistArtifactReference.md) | A portable reference to a public Consist Artifact record, including optional ... |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [UUID](UUID.md) |
| Domain Of | [ConsistArtifactReference](ConsistArtifactReference.md) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |
| Required | Yes |
### Slot Characteristics

| Property | Value |
| --- | --- |
| Owner | [ConsistArtifactReference](ConsistArtifactReference.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/consist/provenance




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | https://w3id.org/consist/provenance/artifact_id |
| native | https://w3id.org/consist/provenance/artifact_id |




## LinkML Source

<details>
```yaml
name: artifact_id
description: The public Consist Artifact.id UUID.
from_schema: https://w3id.org/consist/provenance
rank: 1000
owner: ConsistArtifactReference
domain_of:
- ConsistArtifactReference
range: UUID
required: true

```
</details></div>