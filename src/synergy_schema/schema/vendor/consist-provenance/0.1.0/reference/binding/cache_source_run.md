---
search:
  boost: 5.0
---

# Slot: cache_source_run 


_The historical producer reused for a cache hit. It is absent for a cache miss and resolves to effective_execution_run for a cache hit._



<div data-search-exclude markdown="1">



URI: [https://w3id.org/consist/binding/cache_source_run](https://w3id.org/consist/binding/cache_source_run)
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
| self | https://w3id.org/consist/binding/cache_source_run |
| native | https://w3id.org/consist/binding/cache_source_run |




## LinkML Source

<details>
```yaml
name: cache_source_run
description: The historical producer reused for a cache hit. It is absent for a cache
  miss and resolves to effective_execution_run for a cache hit.
from_schema: https://w3id.org/consist/binding
rank: 1000
owner: ConsistBindingInvocationReference
domain_of:
- ConsistBindingInvocationReference
range: ConsistRunReference
inlined: true

```
</details></div>