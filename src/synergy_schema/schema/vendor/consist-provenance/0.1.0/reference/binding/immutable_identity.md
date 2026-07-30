---
search:
  boost: 5.0
---

# Slot: immutable_identity 


_A trusted typed immutable identity, when Consist can attest one. It must not be inferred from a broader Artifact.hash alone._



<div data-search-exclude markdown="1">



URI: [https://w3id.org/consist/binding/immutable_identity](https://w3id.org/consist/binding/immutable_identity)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [ConsistArtifactReference](ConsistArtifactReference.md) | A portable reference to a public Consist Artifact record, including optional ... |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [ConsistArtifactIdentity](ConsistArtifactIdentity.md) |
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


* from schema: https://w3id.org/consist/binding




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | https://w3id.org/consist/binding/immutable_identity |
| native | https://w3id.org/consist/binding/immutable_identity |




## LinkML Source

<details>
```yaml
name: immutable_identity
description: A trusted typed immutable identity, when Consist can attest one. It must
  not be inferred from a broader Artifact.hash alone.
from_schema: https://w3id.org/consist/binding
rank: 1000
owner: ConsistArtifactReference
domain_of:
- ConsistArtifactReference
range: ConsistArtifactIdentity
inlined: true

```
</details></div>