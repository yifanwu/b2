from functools import reduce
from typing import Optional, Dict, cast
from datascience.tables import Table
from pandas.api.types import is_string_dtype, is_numeric_dtype, is_datetime64_any_dtype 

from midas.midas_algebra.dataframe import GroupBy, MidasDataFrame, RelationalOp, RelationalOpType
from midas.util.errors import type_check_with_warning, InternalLogicalError
from midas.vis_types import EncodingSpec

def get_selectable_column(mdf: MidasDataFrame):
    # if anything is the result of groupby aggregation
    columns_grouped = []
    def walk(ops: RelationalOp):
        if ops.op_type == RelationalOpType.groupby:
            g_op = cast(GroupBy, ops)
            # g_op.columns is a union type of str and array of strings (for developer convenience)
            # FIXME: maybe just make everything array of strings instead...
            if isinstance(g_op.columns, str):
                columns_grouped.append(set([g_op.columns]))
            else:
                columns_grouped.append(set(g_op.columns))
        if ops.has_child():
            walk(ops.child)
        else:
            return
    walk(mdf.ops)
    original_columns = reduce(lambda a, b: a.intersection(b), columns_grouped)
    final_columns = mdf.table.labels
    result = original_columns.intersection(set(final_columns))
    return result


def toggle_x_y(selection_dimensions: str):
    if selection_dimensions == "x":
        return "y"
    elif selection_dimensions == "y":
        return "x"
    else:
        return selection_dimensions


def infer_encoding(mdf: MidasDataFrame) -> Optional[EncodingSpec]:
    """Implements basic show me like feature"""
    df = mdf.table
    type_check_with_warning(df, Table)
    df_len = len(df.columns)
    selectable = get_selectable_column(mdf)
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
