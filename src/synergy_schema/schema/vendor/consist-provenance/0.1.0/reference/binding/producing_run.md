---
search:
  boost: 5.0
---

# Slot: producing_run 


_The Consist run that produced this artifact, when one exists. For an output association, this reference must resolve to the associated run. Leave it absent for an external artifact with no producing Consist run._



<div data-search-exclude markdown="1">



URI: [https://w3id.org/consist/binding/producing_run](https://w3id.org/consist/binding/producing_run)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [ConsistArtifactReference](ConsistArtifactReference.md) | A portable reference to a public Consist Artifact record, including optional ... |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [ConsistRunReference](ConsistRunReference.md) |
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
| self | https://w3id.org/consist/binding/producing_run |
| native | https://w3id.org/consist/binding/producing_run |




## LinkML Source

<details>
```yaml
name: producing_run
description: The Consist run that produced this artifact, when one exists. For an
  output association, this reference must resolve to the associated run. Leave it
  absent for an external artifact with no producing Consist run.
from_schema: https://w3id.org/consist/binding
rank: 1000
owner: ConsistArtifactReference
domain_of:
- ConsistArtifactReference
range: ConsistRunReference
inlined: true

```
</details></div>