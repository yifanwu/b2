from pandas import DataFrame, Series, cut
from typing import Dict, Optional
from midas.defaults import DEFAULT_DATA_SOURCE, Y_DOMAIN_BY_DATA_SIGNAL, COUNT_COL_NAME
from midas.vis_types import ChartInfo, Channel


def get_categorical_distribution(data: Series, column_name: str) -> Optional[DataFrame]:
    # TODO: just select the top 10
    if not data.empty:
        return data.value_counts().to_frame(COUNT_COL_NAME).rename_axis(column_name).reset_index()
    else:
        return None


def get_numeric_distribution(data: Series,  column_name: str) -> Optional[DataFrame]:
    # wow can just use pd.cut
    # FIXME: preserve integer bounds when applicable
    if not data.empty:
        return cut(data, bins=10) \
          .value_counts() \
          .to_frame(COUNT_COL_NAME) \
          .rename_axis(column_name) \
          .reset_index()
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

