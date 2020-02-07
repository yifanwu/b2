# Data8 datascience module instrumentation

## loader functions

These are fine

- `from_rows`
- `from_records`
- `read_table`
- `from_df`
- `from_array`

## queries

These should also be fine, but some of them are a single value, should they be visualized???

More primitive SQL operators

- `apply`
- `copy`
- `drop` (the compliment of select)
- `sort`
- `pivot_bin` (no idea)
- `stack` (no idea)

Shortcuts to SQL functions --- for all of these, we are just going to return normal tables?

- `num_rows`
- `first`
- `stats`
- `percentile`
- `bin`

**Queries that are usually done once**
And they do not tend to participate in queries since you probably do not want to this many times, these are not instrumented. When they are returned, they are returned as a normal, un-instrumented table, if if the user wants to do something with this, they would have to register it back in again.
> maybe talk to joe/arvind about this.

- `sample`
- `shuffle`
- `sample_from_distribution`
- `split`

## Accessors

These we support on the API level, but are not part of our context

- `rows`
- `row`
- `labels`
- `num_columns`
- `column`
- `values`
- `column_index`

- `plot`
- `bar`
- `group_bar`
- `barh`
- `group_barh`
- `scatter`
- `hist`
- `hist_of_counts`
- `boxplot`

## Mutations

- `append`
- `append_column`
- `remove` (this removes rows)
- `relabel`
- `move_to_start`
- `move_to_end`


**that has nothing to do with the core data**

- `set_format`

