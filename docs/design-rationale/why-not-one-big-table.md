# Why not one big table?

A single universal table looks simpler because every field is in one place.
That simplicity falls apart once different models own different columns, the
population changes over time, and one workflow translates data for another.

One wide table would blur four distinctions:

- shared IDs versus model-specific attributes;
- a household or person in one year versus the same one tracked across years;
- the reviewed mapping rules versus the code that applies them; and
- a reusable definition versus evidence from one run.

Separate records keep those lines visible. They also let a model add fields or
change how it stores data without every internal change becoming a change to
the shared definitions.
