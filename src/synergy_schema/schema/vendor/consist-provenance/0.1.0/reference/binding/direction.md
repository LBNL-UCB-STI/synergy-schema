---
search:
  boost: 5.0
---

# Slot: direction 


_Whether the run used the artifact as an input or output._



<div data-search-exclude markdown="1">



URI: [https://w3id.org/consist/binding/direction](https://w3id.org/consist/binding/direction)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [ConsistRunArtifactAssociation](ConsistRunArtifactAssociation.md) | A durable input or output relationship between a run and an artifact |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [ConsistRunArtifactDirection](ConsistRunArtifactDirection.md) |
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
| self | https://w3id.org/consist/binding/direction |
| native | https://w3id.org/consist/binding/direction |




## LinkML Source

<details>
```yaml
name: direction
description: Whether the run used the artifact as an input or output.
from_schema: https://w3id.org/consist/binding
rank: 1000
owner: ConsistRunArtifactAssociation
domain_of:
- ConsistRunArtifactAssociation
range: ConsistRunArtifactDirection
required: true

```
</details></div>