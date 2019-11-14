from datascience import Table
import numpy as np
from math import log10, pow
from typing import Optional
from pandas import notnull

from .errors import InternalLogicalError
from midas.defaults import COUNT_COL_NAME
from midas.vis_types import DfTransform
from midas.util.errors import type_check_with_warning



def transform_df(transform: DfTransform, df: Table):
    type_check_with_warning(df, Table)
    # check ty
    first_col = df.labels[0]
    if (transform == DfTransform.categorical_distribution):
        # sum is the default
        return df.group(first_col)
        # return get_categorical_distribution(df[first_col], first_col)
    elif (transform == DfTransform.numeric_distribution):
        return get_numeric_distribution(df)

def get_chart_title(df_name: str):
    # one level of indirection in case we need to change in the future
    return df_name


# def get_selection_by_predicate(df_info: DFInfo, history_index: int) -> Optional[SelectionEvent]:
#     check_not_null(df_info)
#     if (len(df_info.predicates) > history_index):
#         predicate = df_info.predicates[history_index]
#         return predicate
#     else:
#         return None


MAX_BINS = 20

# def get_categorical_distribution(data: Table, column_name: str) -> Optional[DataFrame]:
#     # TODO: just select the top 10
#     if not data.empty:
#         return data.value_counts().to_frame(COUNT_COL_NAME).rename_axis(column_name).reset_index()
#     else:
#         return None

    # def get_bins(data: Series):


def snap_to_nice_number(n: float):
    if n <= 0:
        raise InternalLogicalError(f"Got {n}")
    if (n <= 1):
        zeroes = pow(10, abs(int(log10(n))) + 1)
        new_num = snap_to_nice_number(n * zeroes)
        return new_num/zeroes
        # if it's less than 1, make it as big as one and then call the same function and return
    if (n <= 2):
        return 2
    elif (n <= 5):
        return 5
    elif (n <= 10):
        return 10
    # bigger than 10, just zero out the digits
    zeroes = pow(10, int(log10(n)))
    return (int(n / zeroes) + 1) * zeroes


def get_numeric_distribution(table: Table) -> Table:
    type_check_with_warning(table, Table)
    first_col = table.labels[0]
    column = table.column(first_col)
    unique_vals = np.unique(column)
    current_max_bins = len(unique_vals)
    if (current_max_bins < MAX_BINS):
        # no binning needed
        return table.group(first_col)
    else:
        min_bucket_count = round(MAX_BINS/current_max_bins)
        d_max = unique_vals[-1]
        d_min = unique_vals[0]
        min_bucket_size = (d_max - d_min) / min_bucket_count
        bound = snap_to_nice_number(min_bucket_size)
        d_nice_min = int(d_min/bound) * bound
        bins = [d_nice_min]
        cur = d_nice_min
        while (cur < d_max):
            cur += bound
            bins.append(cur)
        # def binne_val(v):
        count_col, name_col = np.histogram(column, bins)
        return Table().with_columns({
          first_col: name_col,
          COUNT_COL_NAME: count_col  
        })

        # 
            # return cut(data, bins=bins, labels=bins[1:]) \
            #             .value_counts() \
            #             .to_frame(COUNT_COL_NAME) \
            #             .rename_axis(column_name) \
            #             .reset_index() \
            #             .sort_values(by=[column_name])




# TODO: we need to test this...
def sanitize_dataframe(df: Table):
    """Sanitize a DataFrame to prepare it for serialization.
    
    copied from the ipyvega project
    * Make a copy
    * Convert categoricals to strings.
    * Convert np.bool_ dtypes to Python bool objects
    * Convert np.int dtypes to Python int objects
    * Convert floats to objects and replace NaNs/infs with None.
    * Convert DateTime dtypes into appropriate string representations
    """
    import numpy as np

    if df is None:
        raise InternalLogicalError("Cannot sanitize empty df")

    df = df.copy()

    def to_list_if_array(val):
        if isinstance(val, np.ndarray):
            return val.tolist()
        else:
            return val

    for col_name in df.labels:
        dtype = df.column(col_name).dtype
        if str(dtype) == 'category':
            # XXXX: work around bug in to_json for categorical types
            # https://github.com/pydata/pandas/issues/10778
            df[col_name] = df[col_name].astype(str)
        elif str(dtype) == 'bool':
            # convert numpy bools to objects; np.bool is not JSON serializable
            df[col_name] = df[col_name].astype(object)
        elif np.issubdtype(dtype, np.integer):
            # convert integers to objects; np.int is not JSON serializable
            df[col_name] = df[col_name].astype(object)
        elif np.issubdtype(dtype, np.floating):
            # For floats, convert to Python float: np.float is not JSON serializable
            # Also convert NaN/inf values to null, as they are not JSON serializable
            col = df[col_name]
            bad_values = np.isnan(col) | np.isinf(col)
            df[col_name] = col.astype(object)[bad_values]= None
        elif str(dtype).startswith('datetime'):
            # Convert datetimes to strings
            # astype(str) will choose the appropriate resolution
            new_column = df[col_name].astype(str)
            new_column[new_column == 'NaT'] = ''
            df[col_name] = new_column
        elif dtype == object:
            # Convert numpy arrays saved as objects to lists
            # Arrays are not JSON serializable
            col = np.vectorize(to_list_if_array)(df[col_name])
            col[notnull(col)] = None
            df[col_name] = col.astype(object)
    return df


def dataframe_to_dict(df: Table):
    clean_df = sanitize_dataframe(df)
    def s(x):
        k = {}
        for i, v in enumerate(x):
            k[clean_df.labels[i]] = v
        return k
    return list(map(s, clean_df.rows))
    # return clean_df.to_dict(orient='records')



def prepare_spec(spec, data=None):
    """Prepare a Vega-Lite spec for sending to the frontend.

    This allows data to be passed in either as part of the spec
    or separately. If separately, the data is assumed to be a
    pandas DataFrame or object that can be converted to to a DataFrame.

    Note that if data is not None, this modifies spec in-place
    """
    import pandas as pd

    if isinstance(data, pd.DataFrame):
        # We have to do the isinstance test first because we can't
        # compare a DataFrame to None.
        # data = sanitize_dataframe(data)
        spec['data'] = {'values': dataframe_to_dict(data)}
    elif data is None:
        # Assume data is within spec & do nothing
        # It may be deep in the spec rather than at the top level
        pass
    else:
        # As a last resort try to pass the data to a DataFrame and use it
        data = pd.DataFrame(data)
        spec['data'] = {'values': dataframe_to_dict(data)}
    return spec