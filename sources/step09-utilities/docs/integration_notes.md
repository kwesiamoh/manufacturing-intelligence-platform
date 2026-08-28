# Integration notes

## What this step adds
This is the first source in the project that directly supplies real industrial:
- steam flow;
- steam pressure;
- compressed-air flow;
- compressed-air pressure.

## What it does not add
The source does not, from the accessible metadata alone, justify assigning:
- utility measurements to the fictional European sites;
- utility cost;
- product/SKU;
- production order;
- OEE;
- specific equipment failures;
- CO2 emissions.

Those fields must remain separate unless a later source or explicit synthetic integration model supports them.

## Recommended later Silver schema
After inspecting the downloaded workbook structure, normalize each source table into a long-form table
only if the timestamp, point/node identifier, unit, and value semantics can be verified from the files.

Potential target fields (not to be fabricated):
`timestamp`, `utility_type`, `measurement_type`, `node_id`, `value`, `unit`, `source_file`.

Do not create any of those fields unless the source workbook contains enough evidence to map them correctly.
