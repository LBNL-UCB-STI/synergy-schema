# Consist cache-aware binding invocations

Optional cache-aware invocation facts for portable Consist provenance. This module imports the durable provenance graph without exporting opaque binding evidence or operational observations.

URI: https://w3id.org/consist/binding

Name: consist_binding



## Classes

| Class | Description |
| --- | --- |
| [ConsistArtifactIdentity](ConsistArtifactIdentity.md) | A trusted, typed immutable identity that Consist can attest for a strict boun... |
| [ConsistArtifactReference](ConsistArtifactReference.md) | A portable reference to a public Consist Artifact record, including optional ... |
| [ConsistBindingInvocationReference](ConsistBindingInvocationReference.md) | One resolved binding invocation |
| [ConsistProvenanceContext](ConsistProvenanceContext.md) | The ledger context for portable Consist references |
| [ConsistProvenanceDocument](ConsistProvenanceDocument.md) | A portable provenance handoff with one enclosing ledger context and graph fac... |
| [ConsistRunArtifactAssociation](ConsistRunArtifactAssociation.md) | A durable input or output relationship between a run and an artifact |
| [ConsistRunIdentityEvidence](ConsistRunIdentityEvidence.md) | Optional cache-identity components copied from a Consist Run for audit |
| [ConsistRunReference](ConsistRunReference.md) | A portable reference to a public Consist Run record |



## Slots

| Slot | Description |
| --- | --- |
| [algorithm](algorithm.md) | The attested immutable identity algorithm |
| [artifact](artifact.md) | The consumed or produced Consist artifact |
| [artifact_id](artifact_id.md) | The public Consist Artifact |
| [artifact_key](artifact_key.md) | The human-readable Consist artifact key, when known |
| [artifacts](artifacts.md) | Artifact references carried by this provenance handoff |
| [associations](associations.md) | Consumption and production graph edges carried by this handoff |
| [binding_identity_digest](binding_identity_digest.md) | The optional SHA-256 digest of Consist's strict resolved-binding identity |
| [binding_parameter](binding_parameter.md) | The invocation binding parameter for the artifact, when known |
| [cache_outcome](cache_outcome.md) | The cache outcome for this invocation |
| [cache_source_run](cache_source_run.md) | The historical producer reused for a cache hit |
| [config_hash](config_hash.md) | The run configuration hash, when available |
| [digest](digest.md) | The immutable identity digest |
| [direction](direction.md) | Whether the run used the artifact as an input or output |
| [effective_execution_run](effective_execution_run.md) | The run that supplied the execution result |
| [fingerprint](fingerprint.md) | The public Artifact |
| [fingerprint_strategy](fingerprint_strategy.md) | The hashing strategy or interpretation for fingerprint, when known |
| [git_hash](git_hash.md) | The code revision hash recorded by the run, when available |
| [identity_evidence](identity_evidence.md) | Optional structured run cache-identity evidence |
| [immutable_identity](immutable_identity.md) | A trusted typed immutable identity, when Consist can attest one |
| [input_hash](input_hash.md) | The run input hash, when available |
| [is_implicit](is_implicit.md) | Whether Consist discovered this relationship implicitly, when that evidence i... |
| [kind](kind.md) | The attested immutable identity contract |
| [locator](locator.md) | An optional mutable hint for locating the ledger |
| [model_name](model_name.md) | The Consist model or workflow name, when available |
| [namespace](namespace.md) | A stable logical identifier for the Consist provenance ledger |
| [parent_artifact](parent_artifact.md) | The parent container artifact, when this artifact is a member |
| [parent_run](parent_run.md) | The parent Consist run for a nested execution, when one exists |
| [producing_run](producing_run.md) | The Consist run that produced this artifact, when one exists |
| [provenance_context](provenance_context.md) | The enclosing context inherited by any contained run or artifact reference th... |
| [requested_run](requested_run.md) | The run created for the current invocation |
| [role](role.md) | The invocation-specific semantic role of the artifact, when known |
| [run](run.md) | The consuming or producing Consist run |
| [run_id](run_id.md) | The public Consist Run |
| [runs](runs.md) | Run references carried by this provenance handoff |
| [signature](signature.md) | The Consist run signature when available |


## Enumerations

| Enumeration | Description |
| --- | --- |
| [ConsistArtifactIdentityAlgorithm](ConsistArtifactIdentityAlgorithm.md) | Algorithms Consist can currently attest for immutable artifacts |
| [ConsistBindingCacheOutcome](ConsistBindingCacheOutcome.md) | Whether this invocation executed or reused a cached producer |
| [ConsistRunArtifactDirection](ConsistRunArtifactDirection.md) | Whether a run consumed or produced an artifact |


## Types

| Type | Description |
| --- | --- |
| [boolean](boolean.md) | A binary (true or false) value |
| [ConsistArtifactIdentityKind](ConsistArtifactIdentityKind.md) | Immutable artifact identity contracts Consist can currently attest |
| [curie](curie.md) | a compact URI |
| [date](date.md) | a date (year, month and day) in an idealized calendar |
| [date_or_datetime](date_or_datetime.md) | Either a date or a datetime |
| [datetime](datetime.md) | The combination of a date and time |
| [decimal](decimal.md) | A real number with arbitrary precision that conforms to the xsd:decimal speci... |
| [double](double.md) | A real number that conforms to the xsd:double specification |
| [float](float.md) | A real number that conforms to the xsd:float specification |
| [integer](integer.md) | An integer |
| [jsonpath](jsonpath.md) | A string encoding a JSON Path |
| [jsonpointer](jsonpointer.md) | A string encoding a JSON Pointer |
| [ncname](ncname.md) | Prefix part of CURIE |
| [nodeidentifier](nodeidentifier.md) | A URI, CURIE or BNODE that represents a node in a model |
| [objectidentifier](objectidentifier.md) | A URI or CURIE that represents an object in the model |
| [SHA256Digest](SHA256Digest.md) | A lowercase hexadecimal SHA-256 digest |
| [sparqlpath](sparqlpath.md) | A string encoding a SPARQL Property Path |
| [string](string.md) | A character string |
| [time](time.md) | A time object represents a (local) time of day, independent of any particular... |
| [uri](uri.md) | a complete URI |
| [uriorcurie](uriorcurie.md) | a URI or a CURIE |
| [UUID](UUID.md) | A canonical RFC 4122 UUID string |


## Subsets

| Subset | Description |
| --- | --- |
