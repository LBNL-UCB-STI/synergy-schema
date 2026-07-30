---
search:
  boost: 5.0
---

# Slot: requested_run 


_The run created for the current invocation._



<div data-search-exclude markdown="1">



URI: [https://w3id.org/consist/binding/requested_run](https://w3id.org/consist/binding/requested_run)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [ConsistBindingInvocationReference](ConsistBindingInvocationReference.md) | One resolved binding invocation |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [ConsistRunReference](ConsistRunReference.md) |
| Domain Of | [ConsistBindingInvocationReference](ConsistBindingInvocationReference.md) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |
| Required | Yes |
### Slot Characteristics

| Property | Value |
| --- | --- |
| Owner | [ConsistBindingInvocationReference](ConsistBindingInvocationReference.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/consist/binding




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | https://w3id.org/consist/binding/requested_run |
| native | https://w3id.org/consist/binding/requested_run |




## LinkML Source

<details>
```yaml
name: requested_run
description: The run created for the current invocation.
from_schema: https://w3id.org/consist/binding
rank: 1000
owner: ConsistBindingInvocationReference
domain_of:
- ConsistBindingInvocationReference
range: ConsistRunReference
required: true
inlined: true

```
</details></div>