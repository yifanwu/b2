# Midas Algebra

We implement simple dataframe functions (the relation algebra compatible subset).

We chose not to instrument pandas due to the difficult, but the execution will return pandas dataframes which can use pandas operations.  For future interactions, we can also connect with backend databases.

__Problem Statement__: given a predicate, apply the selection to a query AST to transform it.

## Algorithmic Method for Applying Selections

There two steps then for applying the selections:

1. compute the relation to be replaced with
2. replace the old relation with the new in the target AST

Credit: thanks to [Brian Hempel](http://people.cs.uchicago.edu/~brianhempel/) for his constructive input.

## Running in Dev mode

Currently, `midas_algebra` is co-developed with the `midas` repo, and you can run the code from a notebook environment by following the set up instructions in the readme of the `midas` repo.

## Engineering Note

We wrap around the [datascience](https://github.com/data-8/datascience) library implemented by the Berkeley data-8 team.