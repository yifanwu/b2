from typing import cast
from .types import OneDimSelectionPredicate, SelectionPredicate
from pandas import DataFrame

def get_df_by_predicate(df: DataFrame, predicate: SelectionPredicate):
    """get_selection returns the selection DF
    The default would be the selection of all of the df
    However, if some column is not in the rows of the df are specified, Midas will try to figure out based on the derivation history what is going on.
    
    Arguments:
        df_name {str} -- [description]
    
    Returns:
        [type] -- [description]
    """
    # Maybe TODO: with the optional columns specified

    if (isinstance(predicate, OneDimSelectionPredicate)):
        # FIXME: the story around categorical is not clear
        _p = cast(OneDimSelectionPredicate, predicate)
        if (_p.is_categoritcal):
            selection_df = df.loc[
                df[predicate.x_column].isin(_p.x)
            ]
        else:
            selection_df = df.loc[
                (df[predicate.x_column] < predicate.x[1])
                & (df[predicate.x_column] > predicate.x[0])
            ]
        return selection_df
    else:
        selection_df = df.loc[
                (df[predicate.x_column] < predicate.x[1])
            & (df[predicate.x_column] > predicate.x[0])
            & (df[predicate.y_column] > predicate.y[0])
            & (df[predicate.y_column] < predicate.y[1])
        ]
        return selection_df
