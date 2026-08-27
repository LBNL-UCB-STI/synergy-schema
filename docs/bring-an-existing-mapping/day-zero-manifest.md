# Day-zero manifest

A day-zero manifest records one existing payload and the code or run that
produced it. It answers the first practical questions—what file is being
discussed, which exact bytes does it contain, and where did it come from—before
any claim is made about a complete field mapping or runtime integration.

This is discovery evidence. It prevents later review from drifting to a
different file with the same name, but it does not establish that the payload
is correct or that an automatic adapter exists.

The first acceptance point is deliberately narrow: the payload and producer
identities are present and the manifest passes its structural check. Work stops
before mapping claims are recorded when a representative payload or its source
cannot be identified. Automatic receipt emission is a later production goal;
manual discovery remains an honest description of the current state.
