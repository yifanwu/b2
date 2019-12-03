from typing import Optional, Dict
from datascience.tables import Table
from pandas.api.types import is_string_dtype, is_numeric_dtype, is_datetime64_any_dtype 

from midas.midas_algebra.dataframe import MidasDataFrame
from midas.util.errors import type_check_with_warning, InternalLogicalError
from midas.vis_types import EncodingSpec

def infer_encoding(mdf: MidasDataFrame) -> Optional[EncodingSpec]:
    """Implements basic show me like feature
        if there is only one column, try to do a distribution with reasonable binning
        if one categorical, one numeric, barchart
        , unless if one is time, then line (line, todo)
    """
    df = mdf.table
    type_check_with_warning(df, Table)
    # error if df has no column
    df_len = len(df.columns)
    # additional_transforms: Optional[DfTransform] = None
    if (df_len == 0):
        raise Exception("DataFrame has too few columns")
    elif df_len == 1:
        return None
    elif df_len == 2:
        first_col = df.labels[0]
        # fow now let's just take the frist two columns
        second_col = df.labels[1]
        if is_string_dtype(df[first_col]) and is_numeric_dtype(df[second_col]):
            return EncodingSpec("bar", first_col, second_col)
        elif is_numeric_dtype(df[first_col]) and is_string_dtype(df[second_col]):
            return EncodingSpec("bar", second_col, first_col)
        elif is_numeric_dtype(df[first_col]) and is_numeric_dtype(df[second_col]):
            # if two numeric, scatter
            return EncodingSpec("circle", first_col, second_col)
        elif is_datetime64_any_dtype(df[first_col]) and is_numeric_dtype(df[second_col]):
            return EncodingSpec("line", first_col, second_col)
        raise InternalLogicalError(f"Corner case in spec gen")
    else:
        raise InternalLogicalError(f"don't know how to handler more than 3 cases")

