from pandas import DataFrame
from typing import cast, Optional

from .types import OneDimSelectionPredicate, SelectionPredicate, NullSelectionPredicate
from .constants import CUSTOM_INDEX_NAME


def get_df_transform_func_by_index(target_df: DataFrame):
    # basically add a 
    def transform(df_in: DataFrame):
        import pandas as pd
        return pd.merge(target_df, df_in, how="inner", on=CUSTOM_INDEX_NAME)
    return transform


def get_df_by_predicate(df: DataFrame, predicate: SelectionPredicate):
    """get_selection returns the selection DF
    it's optional because the selection could have churned out "null"
    The default would be the selection of all of the df
    However, if some column is not in the rows of the df are specified, Midas will try to figure out based on the derivation history what is going on.
    
    Arguments:
        df_name {str} -- [description]
    
    Returns:
        [type] -- [description]
    """
    # Maybe TODO: with the optional columns specified
    if (isinstance(predicate, NullSelectionPredicate)):
        # in case the user modifies the dataframe
        return df.copy()
    elif (isinstance(predicate, OneDimSelectionPredicate)):
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
