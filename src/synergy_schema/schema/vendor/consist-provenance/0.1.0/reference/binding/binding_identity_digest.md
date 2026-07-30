---
search:
  boost: 5.0
---

# Slot: binding_identity_digest 


_The optional SHA-256 digest of Consist's strict resolved-binding identity. It identifies a binding contract, not opaque evidence JSON._



<div data-search-exclude markdown="1">



URI: [https://w3id.org/consist/binding/binding_identity_digest](https://w3id.org/consist/binding/binding_identity_digest)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [ConsistBindingInvocationReference](ConsistBindingInvocationReference.md) | One resolved binding invocation |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [SHA256Digest](SHA256Digest.md) |
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
| self | https://w3id.org/consist/binding/binding_identity_digest |
| native | https://w3id.org/consist/binding/binding_identity_digest |




## LinkML Source

<details>
```yaml
name: binding_identity_digest
description: The optional SHA-256 digest of Consist's strict resolved-binding identity.
  It identifies a binding contract, not opaque evidence JSON.
from_schema: https://w3id.org/consist/binding
rank: 1000
owner: ConsistBindingInvocationReference
domain_of:
- ConsistBindingInvocationReference
range: SHA256Digest

```
</details></div>