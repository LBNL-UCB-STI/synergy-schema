# Why not one big table?

A universal table looks simpler because every field appears in one place. The
simplicity disappears once different models own different columns, populations
change over time, and one workflow translates data for another.

One wide table would blur four distinctions:

- shared identity versus model-specific attributes;
- one population occurrence versus a longitudinal entity;
- reviewed mapping rules versus the code that applies them; and
- a reusable definition versus evidence from one run.

Separate records keep those boundaries visible. They also allow a native model
to add fields or change internal storage without turning every local revision
into a change to the shared universe.
