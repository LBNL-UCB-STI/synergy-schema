# Mappings

Mappings explain how two definitions relate without replacing or copying
either one. A mapping might say that:

- two fields have the same meaning but different names;
- a value needs a unit or code conversion;
- a destination value is calculated from several source fields;
- a source field has no equivalent in the destination.

Mappings connect shared concepts, model-owned schemas, and workflow profiles.
They make conversions and unsupported fields visible rather than suggesting
that similar-looking data is automatically interchangeable.

`population_identity.yaml` defines the typed vocabulary for mapping
identity-bearing population records. The canonical post-ATLAS manifest is
[`../../../../examples/post_atlas_population_bundle/population_identity_mappings.yaml`](../../../../examples/post_atlas_population_bundle/population_identity_mappings.yaml).
Each entry records source and target paths, transformation status, identity
role, value stability, and repository-relative evidence for the observed
PILATES behavior.
