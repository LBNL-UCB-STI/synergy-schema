# Why LinkML

The shared definitions need to be readable as source files, precise enough to
validate against, and able to generate a browsable field reference. LinkML
does all three, and the models never have to use it at runtime.

The LinkML files define structure: fields, types, required values, and
relationships. Python checks handle comparisons across files, such as whether
a receipt names the same scenario and mapping as its bundle. The models
themselves remain responsible for producing and reading their own data.

This split keeps the shared definitions portable, without passing off schema
validation as proof that a whole workflow ran correctly.
