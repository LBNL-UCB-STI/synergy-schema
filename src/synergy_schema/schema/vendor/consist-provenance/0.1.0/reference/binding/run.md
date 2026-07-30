---
search:
  boost: 5.0
---

# Slot: run 


_The consuming or producing Consist run._



<div data-search-exclude markdown="1">



URI: [https://w3id.org/consist/binding/run](https://w3id.org/consist/binding/run)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [ConsistRunArtifactAssociation](ConsistRunArtifactAssociation.md) | A durable input or output relationship between a run and an artifact |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [ConsistRunReference](ConsistRunReference.md) |
| Domain Of | [ConsistRunArtifactAssociation](ConsistRunArtifactAssociation.md) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |
| Required | Yes |
### Slot Characteristics

| Property | Value |
| --- | --- |
| Owner | [ConsistRunArtifactAssociation](ConsistRunArtifactAssociation.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/consist/binding




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | https://w3id.org/consist/binding/run |
| native | https://w3id.org/consist/binding/run |




## LinkML Source

<details>
```yaml
name: run
description: The consuming or producing Consist run.
from_schema: https://w3id.org/consist/binding
rank: 1000
owner: ConsistRunArtifactAssociation
domain_of:
- ConsistRunArtifactAssociation
range: ConsistRunReference
required: true
inlined: true

```
</details></div>