# Midas Tutorial

## Decorated functions

`read_csv`

`read_json`

`m_loc`

## Linking logic

Can access via `new_visualization_from_selection`, which takes in DF

Potentially could also take selection via predicates?

## Opinionated

To get certain subsets of a dataframe, Pandas allows the developer many different ways.  For instance, just in `loc`, there are [many](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.loc.html) ways.

In _Midas_, the methods are a lot more restricted. `loc` is used for slicing, and `apply` is used for applying functional transformations, `groupby` and `joins` are also captured.

```python
m = Midas()
# in pandas
# the DFs are referenced by name so we can manage the associated attrviutes, such as the visualization easier
m.loc('original_df', 'new_df', rows = [0: 2], column = ['col1', 'col3'])

# returns boolean values (basically the two axis of apply)
m.filter_rows('original_df', 'new_df', func = lambda r: r['col1'] > 10)
m.new_column('original_df', 'new_df', func = lambda: r['col1'] + r['col2'], column_name = 'new_col')
```

```python
countries = ['China', 'Japan']
# or equivalently
df.loc[df['Origin'] == 'USA']
# in Midas
rows = df['shield'] == 8
df.apply(lambda x: [1, 2], axis=1)
columns = None
```
