from typing import Dict, Optional, List, Callable, Union, cast
from pandas import DataFrame

from midas.vis_types import OneDimSelectionPredicate, SelectionPredicate, NullSelectionPredicate, TwoDimSelectionPredicate

def get_raw_df_code_by_predicate(predicate: SelectionPredicate, df_name: str):
    # note that this code closely mirrors that in get_df_by_predicate
    t_str = predicate.interaction_time.strftime("%m_%d_%H_%M_%S")
    meta_data_str=f"""# generated from interaction on `{df_name}` at time {t_str}"""
    if (isinstance(predicate, OneDimSelectionPredicate)):
        # FIXME: the story around categorical is not clear
        _p = cast(OneDimSelectionPredicate, predicate)
        if (_p.is_categoritcal):
            return f"""{meta_data_str}\n{df_name}.loc[{df_name}['{predicate.x_column}'].isin({predicate.x})]"""
        else:
            return f"""{meta_data_str}\n{df_name}.loc[\n({df_name}['{predicate.x_column}'] < {predicate.x[1]})\n& ({df_name}['{predicate.x_column}'] > {predicate.x[0]})]"""
    elif(isinstance(predicate, TwoDimSelectionPredicate)):
        return f"""{meta_data_str}\n{df_name}.loc[\n({df_name}['{predicate.x_column}'] < {predicate.x[1]})\n& ({df_name}['{predicate.x_column}'] > {predicate.x[0]})\n& ({df_name}['{predicate.y_column}'] > {predicate.y[0]})\n& ({df_name}['{predicate.y_column}'] < {predicate.y[1]})\n]"""
    else:
        return ""


# def get_derived_df_code(source_df: str, target_df: str, derivation: DFDerivation):
#     return ""
