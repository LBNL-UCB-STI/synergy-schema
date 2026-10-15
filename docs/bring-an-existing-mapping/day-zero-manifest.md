# Day-zero manifest

A day-zero manifest records one existing file and the code or run that
produced it. It answers the first practical questions: which file are we
talking about, what exactly is in it, and where did it come from? It does this
before anyone makes claims about a complete field mapping or a runtime
integration.

Think of it as discovery evidence. It stops later reviews from drifting onto a
different file with the same name, but it doesn't show that the file is
correct or that an automatic adapter exists.

The bar for this step is deliberately low: the file and producer fingerprints
are present, and the manifest passes its structural check. Work stops here,
before any mapping is written down, if nobody can find a representative file
or say where it came from. Automatic receipt emission is a later production
goal; until then, assembling the manifest by hand is an honest description of
where things stand.
