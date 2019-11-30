# Developer Experience

## Principles

Transparency---the API should match the underlying algebra.  This will hopefully help create intuition.

## API Design

Developers can directly manipulate the dataframes which will have references to the visualizations created, as well as the events etc.

### Accessing Selections

```python
df_selection_stream = m.selection_stream(df)

# get the predicate
selection = df_selection_stream.get_current()

# get the selection as applied to any DFs
selection.apply_to(df)
```

### Adding to the Event Loop

```python
def reaction_one(selection):
  # use selection
  new_df = selection.apply_to(df)
  return new_df

# reactive_charts must return a dataframe
df_stream.add_reactive_chart(reaction_one)

# the analyst can also add cell magic to rerun cells
%% reactive_cell '<the_df_name>'
```

### Linking Charts

Often, we want to filter one chart based on the selection of another chart.

```python
df2.apply_selection(df)
```

There is a special case of zooming, which is essentially ``self'' linking.

```python
df2.make_zoom()
# which is syntax sugar equivalent to the following
cars_df_predicate_stream.filter(df2)
```

## Midas DataFrame Syntax

In order to automatically propagate selections to charts (dataframes), we need to know the structure of the queries that have derived the underlying dataframe.  We created our own dataframe in order to better track the derivation information.
