from functools import reduce
# from midas.midas_algebra.dataframe import MidasDataFrame, RelationalOpType
from typing import Optional, Dict, cast
from typing_extensions import Literal
from datascience.tables import Table
from pandas.api.types import is_string_dtype, is_numeric_dtype, is_datetime64_any_dtype 
from IPython.core.debugger import set_trace

from midas.util.errors import type_check_with_warning, InternalLogicalError
from midas.vis_types import EncodingSpec


def toggle_x_y(selection_dimensions: Literal["", "x", "y", "xy"]):
    if selection_dimensions == "x":
        return "y"
    elif selection_dimensions == "y":
        return "x"
    else:
        return selection_dimensions


def infer_encoding_helper(df: Table, selectable, is_groupby: bool):
    """infers encoding, subject to more parameters, ideally we pass in all of the operations, but for now, we just need is_groupby, which affects the encoding choices.

    Arguments:
        df {Table} -- [description]
        selectable {[type]} -- [description]
        is_groupby {bool} -- whether the ops were groupby
    """
    df_len = len(df.columns)
    if df_len == 2:
        first_col = df.labels[0]
        second_col = df.labels[1]
        selection_dimensions = ""
        if len(selectable) == 2:
            selection_dimensions = "xy"
        elif len(selectable) == 1 and next(iter(selectable)) == first_col:
             selection_dimensions = "x"
        elif len(selectable) == 1 and next(iter(selectable)) == second_col:
            selection_dimensions = "y"
        elif len(selectable) == 0:
            selection_dimensions = ""
        # check if there was a groupby, special case
        if is_groupby:
            # then the results have to be ordinal
            # whether it's multiclick or brush would depend on whether the value is numeric
            # if its a groupby, can make the assum0ption that the first one is the ordinal value and the second one is the quantitative value
            selection_type = "brush"
            sort = ""

            if is_string_dtype(df[first_col]):
                selection_type = "multiclick"
                # we will arrange it such that it's the second one that's numeric
                sort = "-y"
               
            return EncodingSpec("bar", first_col, "ordinal", second_col, "quantitative", selection_type, selection_dimensions, sort)
        if is_string_dtype(df[first_col]) and is_numeric_dtype(df[second_col]):
            return EncodingSpec("bar", first_col, "ordinal", second_col, "quantitative", "multiclick", selection_dimensions)
        elif is_numeric_dtype(df[first_col]) and is_string_dtype(df[second_col]):
            selection_dimensions = toggle_x_y(selection_dimensions)
            return EncodingSpec("bar", second_col, "ordinal", first_col, "quantitative", "multiclick", selection_dimensions)
        elif is_numeric_dtype(df[first_col]) and is_numeric_dtype(df[second_col]):
            return EncodingSpec("circle", first_col, "quantitative", second_col, "quantitative", "brush", selection_dimensions)
        elif is_datetime64_any_dtype(df[first_col]) and is_numeric_dtype(df[second_col]):
            return EncodingSpec("line", first_col, "temporal", second_col, "quantitative", "brush", selection_dimensions)
        elif is_numeric_dtype(df[first_col]) and is_datetime64_any_dtype(df[second_col]):
            selection_dimensions = toggle_x_y(selection_dimensions)
            return EncodingSpec("line", second_col, "temporal", first_col, "quantitative", "brush", selection_dimensions)
        raise InternalLogicalError(f"Corner case in spec gen")
    else:
        raise InternalLogicalError(f"Midas only supports visualization of two dimensional data for now")
