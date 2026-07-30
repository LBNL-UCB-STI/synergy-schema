# Vendored Consist provenance schema

This directory contains an unchanged Consist LinkML schema release used by the
PILATES operational profile. Model-owned schemas and the shared Synergy kernel
do not import it.

- Schema version: `0.1.0`
- Source repository: <https://github.com/LBNL-UCB-STI/consist>
- Source commit: `55b5b1235c66c740b3963cb4907ec857a2d3f69d`
- Source pull request: <https://github.com/LBNL-UCB-STI/consist/pull/207>
- Imported module: `0.1.0/provenance.yaml`
- Deferred optional module: `0.1.0/binding.merged.yaml`

The modular provenance source is used because it passes the pinned LinkML
linter unchanged and its only import is the locally installed
`linkml:types`. The `0.1.0` merged asset is preserved as part of the upstream
release, but it is not imported because its generated timestamp metadata lacks
the timezone required by the same LinkML linter. A future Consist release may
return the PILATES profile to a merged import after the release builder emits a
lint-clean closure.

The version directory is the direct output of Consist's
`scripts/build_provenance_schema_release.py`. Verify every original release
asset from that directory:

```sh
cd src/synergy_schema/schema/vendor/consist-provenance/0.1.0
shasum -a 256 -c SHA256SUMS
```

Do not edit a vendored version in place. Build and add a new versioned
directory, update the PILATES profile import, and retain the old directory
until no supported Synergy release imports it.
