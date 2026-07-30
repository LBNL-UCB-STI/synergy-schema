---
search:
  boost: 5.0
---

# Slot: fingerprint 


_The public Artifact.hash value. It is a portable fingerprint whose interpretation follows the hashing strategy and may be content- or metadata-based. Artifact.content_id is database-local and is never a portable fingerprint._



<div data-search-exclude markdown="1">



URI: [https://w3id.org/consist/provenance/fingerprint](https://w3id.org/consist/provenance/fingerprint)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [ConsistArtifactReference](ConsistArtifactReference.md) | A portable reference to a public Consist Artifact record, including optional ... |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [string](string.md) |
| Domain Of | [ConsistArtifactReference](ConsistArtifactReference.md) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |
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
| self | https://w3id.org/consist/provenance/fingerprint |
| native | https://w3id.org/consist/provenance/fingerprint |




## LinkML Source

<details>
```yaml
name: fingerprint
description: The public Artifact.hash value. It is a portable fingerprint whose interpretation
  follows the hashing strategy and may be content- or metadata-based. Artifact.content_id
  is database-local and is never a portable fingerprint.
from_schema: https://w3id.org/consist/provenance
rank: 1000
owner: ConsistArtifactReference
domain_of:
- ConsistArtifactReference
range: string

```
</details></div>