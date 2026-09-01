# Why LinkML

The shared language must be readable in source form, precise enough for typed
validation, and able to generate a browsable field reference. LinkML provides
that combination without requiring participating models to adopt it at
runtime.

The LinkML files define structure: fields, types, required values, and declared
relationships. Python conformance checks handle comparisons across files, such
as whether a receipt names the same scenario and mapping as its bundle. Model
runtimes remain responsible for producing and consuming their native data.

This division keeps the portable definitions useful without presenting schema
validation as proof that a full workflow ran correctly.
