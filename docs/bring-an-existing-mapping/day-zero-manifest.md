# Day-zero manifest

The day-zero manifest is discovery-only: it records exact payload and producer
bytes without declaring that a runtime adapter exists. Acceptance criterion:
the receipt has both identities and passes its structural check. The kill criterion:
if the producer cannot identify a representative payload or its source, stop
before encoding semantic claims.

Automatic-emission is a later automatic-emission acceptance criterion for a production receipt;
manual discovery remains honest evidence, not a deployment claim.
