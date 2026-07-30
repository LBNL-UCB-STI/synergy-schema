---
search:
  boost: 5.0
---

# Slot: signature 


_The Consist run signature when available. It supports audit but does not replace run_id as the run reference._



<div data-search-exclude markdown="1">



URI: [https://w3id.org/consist/binding/signature](https://w3id.org/consist/binding/signature)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [ConsistRunReference](ConsistRunReference.md) | A portable reference to a public Consist Run record |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [string](string.md) |
| Domain Of | [ConsistRunReference](ConsistRunReference.md) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |
### Slot Characteristics

| Property | Value |
| --- | --- |
| Owner | [ConsistRunReference](ConsistRunReference.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/consist/binding




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | https://w3id.org/consist/binding/signature |
| native | https://w3id.org/consist/binding/signature |




## LinkML Source

<details>
```yaml
name: signature
description: The Consist run signature when available. It supports audit but does
  not replace run_id as the run reference.
from_schema: https://w3id.org/consist/binding
rank: 1000
owner: ConsistRunReference
domain_of:
- ConsistRunReference
range: string

```
</details></div>