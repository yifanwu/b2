# taken from https://github.com/vega/ipyvega/blob/master/vega/utils.py

import codecs
from os import path

from typing import Tuple, List
from pandas import DataFrame
from IPython import get_ipython

import random
import string

def isnotebook():
    try:
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':
            return True   # Jupyter notebook or qtconsole
        elif shell == 'TerminalInteractiveShell':
            return False  # Terminal running IPython
        else:
            return False  # Other type (?)
    except NameError:
        return False      # Probably standard Python interpreter

# def in_ipynb():
#     try:
#         get_ipython()
#         return True
#     except NameError:
#         return False

# try:
#     from IPython.display import get_ipython
# except ImportError as err:
#     def in_ipynb():
#         return False

def abs_path(p: str):
    """Make path absolute."""
    return path.join(
        path.dirname(path.abspath(__file__)),
        p)

def check_path(p: str):
    if not path.exists(p):
        raise UserWarning(f"The path you provided, {p} does not exists")


def get_content(path):
    """Get content of file."""
    with codecs.open(abs_path(path), encoding='utf-8') as f:
        return f.read()


def sanitize_dataframe(df):
    """Sanitize a DataFrame to prepare it for serialization.

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


def dataframe_to_dict(df: DataFrame):
    clean_df = sanitize_dataframe(df)
    return clean_df.to_dict(orient='records')

ifnone = lambda a, b: b if a is None else a

def get_min_max_tuple_from_list(values: List[float]) -> Tuple[float, float]:
    """sets in place the array if the values are not min and max
    
    Arguments:
        x_value {List[int]} -- [description]
    
    Returns:
       returns the modifed array in place
    """
    if (values[0] > values[1]):
        return (values[1], values[0])
    return (values[0], values[1])