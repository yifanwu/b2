from pandas import DataFrame, Series, cut  # type: ignore
from math import log10, pow
from typing import Optional

from midas.util.errors import InternalLogicalError
from midas.defaults import COUNT_COL_NAME

MAX_BINS = 20

def get_categorical_distribution(data: Series, column_name: str) -> Optional[DataFrame]:
    # TODO: just select the top 10
    if not data.empty:
        return data.value_counts().to_frame(COUNT_COL_NAME).rename_axis(column_name).reset_index()
    else:
        return None

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


def get_numeric_distribution(data: Series,  column_name: str) -> Optional[DataFrame]:
    if not data.empty:
        current_max_bins = data.nunique()
        if (current_max_bins < MAX_BINS):
            # no binning needed
            return data.value_counts() \
                       .to_frame(COUNT_COL_NAME) \
                       .rename_axis(column_name) \
                       .reset_index() \
                       .sort_values(by=[column_name])
        else:
            min_bucket_count = round(MAX_BINS/current_max_bins)
            d_max = data.max()
            d_min = data.min()
            min_bucket_size = (d_max - d_min) / min_bucket_count
            bound = snap_to_nice_number(min_bucket_size)
            d_nice_min = int(d_min/bound) * bound
            bins = [d_nice_min]
            cur = d_nice_min
            while (cur < d_max):
                cur += bound
                bins.append(cur)
                return cut(data, bins=bins, labels=bins[1:]) \
                            .value_counts() \
                            .to_frame(COUNT_COL_NAME) \
                            .rename_axis(column_name) \
                            .reset_index() \
                            .sort_values(by=[column_name])
    else:
        return None



def sanitize_dataframe(df):
    """Sanitize a DataFrame to prepare it for serialization.
    
    copied from the ipyvega project
    * Make a copy
    * Raise ValueError if it has a hierarchical index.
    * Convert categoricals to strings.
    * Convert np.bool_ dtypes to Python bool objects
    * Convert np.int dtypes to Python int objects
    * Convert floats to objects and replace NaNs/infs with None.
    * Convert DateTime dtypes into appropriate string representations
    """
    import pandas as pd
    import numpy as np

    if df is None:
        raise InternalLogicalError("Cannot sanitize empty df")

    df = df.copy()

    if isinstance(df.index, pd.core.index.MultiIndex):
        raise ValueError('Hierarchical indices not supported')
    if isinstance(df.columns, pd.core.index.MultiIndex):
        raise ValueError('Hierarchical indices not supported')

    def to_list_if_array(val):
        if isinstance(val, np.ndarray):
            return val.tolist()
        else:
            return val

    for col_name, dtype in df.dtypes.iteritems():
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
            bad_values = col.isnull() | np.isinf(col)
            df[col_name] = col.astype(object).where(~bad_values, None)
        elif str(dtype).startswith('datetime'):
            # Convert datetimes to strings
            # astype(str) will choose the appropriate resolution
            df[col_name] = df[col_name].astype(str).replace('NaT', '')
        elif dtype == object:
            # Convert numpy arrays saved as objects to lists
            # Arrays are not JSON serializable
            col = df[col_name].apply(to_list_if_array, convert_dtype=False)
            df[col_name] = col.where(col.notnull(), None)
    return df

