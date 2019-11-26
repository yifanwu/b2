# Architecture

We need to coordinate the state in the code with the state in the JS end.

The connection is somewhat deep. For instance, 


## Synchronizing state

There are three ways the charts could update:

- Base data is set/replaced (this requires a full vega replacement)
- Filter data is set/replaced

Also when the base data is being created, we need to see if the filtered data need to be created...
