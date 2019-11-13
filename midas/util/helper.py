from pandas import DataFrame # type: ignore
from typing import cast, Optional
from datetime import datetime
from typing import Dict, Optional

from .data_processing import get_categorical_distribution, get_numeric_distribution
from midas.midas_algebra.dataframe import DFInfo
from midas.defaults import COUNT_COL_NAME
from midas.vis_types import OneDimSelectionPredicate, DfTransform, SelectionEvent, NullSelectionPredicate, DfTransform
from .errors import check_not_null


def transform_df(transform: DfTransform, df: DataFrame):
    first_col = df.columns.values[0]
    if (transform == DfTransform.categorical_distribution):
        return get_categorical_distribution(df[first_col], first_col)
    elif (transform == DfTransform.numeric_distribution):
        return get_numeric_distribution(df[first_col], first_col)
    
def get_chart_title(df_name: str):
    # one level of indirection in case we need to change in the future
    return df_name


def get_selection_by_predicate(df_info: DFInfo, history_index: int) -> Optional[SelectionEvent]:
    check_not_null(df_info)
    if (len(df_info.predicates) > history_index):
        predicate = df_info.predicates[history_index]
        return predicate
    else:
        return None


def get_df_by_predicate(df: DataFrame, predicate: SelectionEvent):
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
