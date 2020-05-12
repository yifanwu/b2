from datascience import Table
import json
import numpy as np
from math import log10, pow, floor
from pandas import notnull
from typing import Tuple
from IPython.core.debugger import set_trace

from midas.constants import ISDEBUG
from .errors import InternalLogicalError
from midas.constants import IS_OVERVIEW_FIELD_NAME, MAX_BINS, STUB_DISTRIBUTION_BIN, MAX_GENERATED_BINS
from midas.vis_types import FilterLabelOptions
from .utils import sanitize_string_for_var_name
from midas.vis_types import EncodingSpec


def get_chart_title(df_name: str):
    # one level of indirection in case we need to change in the future
    return df_name


DATE_HIERARCHY = [
    ("Y", "year"),
    ("M", "month"),
    ("D", "day")
]


# B2DataFrame
def static_vega_gen(encoding: EncodingSpec, df):
    records = dataframe_to_dict(df, FilterLabelOptions.none)
    # data = json.dumps(records)
    if encoding.mark == "bar":
        barSpec = {
            "$schema": "https://vega.github.io/schema/vega-lite/v4.json",
            "height": 200,
            "data": {"values": records},
            "mark": "bar",
            "encoding": {
                "x": {
                    "field": encoding.x,
                    "type": encoding.x_type
                },
                "y": {
                    "field": encoding.y,
                    "type": encoding.y_type,
                },
            }
        }
        if encoding.sort != "":
            barSpec["encoding"]["x"]["sort"] = encoding.sort
        return barSpec
    elif encoding.mark == "circle":
        scatterSpec = {
            "$schema": "https://vega.github.io/schema/vega-lite/v4.json",
            "data": { "values": records },
            "mark": {"type": "point",  "tooltip": 1},
            "encoding": {
                "x": {
                    "field": encoding.x,
                    "type": encoding.x_type,
                    "scale": {"zero": 0}
                },
                "y": {"field": encoding.y, "type": encoding.y_type},
            }
        }
        return scatterSpec
    elif encoding.mark == "line":
        lineSpec = {
            "$schema": "https://vega.github.io/schema/vega-lite/v4.json",
            "data": { "values": records },
            "mark": "line",
            "encoding": {
                "x": {"field": encoding.x, "type": encoding.x_type},
                "y": {"field": encoding.y, "type": encoding.y_type},
            },
        }
        return lineSpec
    else:
        return None


def get_basic_group_vis(new_name, df_name, col_name):
    return f"{new_name} = {df_name}.group('{col_name}')\n{new_name}.vis()"


def create_binning_code(bound, col_name, df_name, new_name, midas_reference_name):
    bin_column_name = f"{col_name}_bin"
    # lambda n: int(n/5) * 5
    if bound < 1:
        round_num = -1 * floor(log10(bound))
        binning_lambda = f"lambda x: 'null' if {midas_reference_name}.np.isnan(x) else round(int(x/{bound}) * {bound}, {round_num})"
    else:
        binning_lambda = f"lambda x: 'null' if {midas_reference_name}.np.isnan(x) else int(x/{bound}) * {bound}"
    bin_transform = f"{df_name}['{bin_column_name}'] = {df_name}.apply({binning_lambda}, '{col_name}')"
    grouping_transform = get_basic_group_vis(new_name, df_name, bin_column_name)
    code = f"{bin_transform}\n{grouping_transform}"
    return code


def try_parsing_date_time_level(ref, col_value, col_name, df_name):
    parsed = col_value.astype(f'datetime64[{ref[0]}]')
    count = len(np.unique(parsed))
    new_col_name = sanitize_string_for_var_name(f"{col_name}_{ref[1]}")
    if count > 1:
        new_column = f"{df_name}['{col_name}_{ref[1]}'] = {df_name}['{col_name}'].astype('datetime64[{ref[0]}]')"
        new_name = f"{df_name}_{new_col_name}_dist"
        if count > MAX_BINS:
            bound = snap_to_nice_number(count/MAX_BINS)
            binning_lambda = f"lambda x: 'null' if np.isnan(x) else int(x/{bound}) * {bound}"
            bin_column_name = f"{new_col_name}_bin"
            bin_transform =  f"{df_name}['{bin_column_name}'] = {df_name}.apply({binning_lambda}, '{col_name}')"
            grouping = get_basic_group_vis(new_name, df_name, new_col_name)
            code = f"{new_column}\n{bin_transform}\n{grouping}"
            return code
        else:
            grouping = get_basic_group_vis(new_name, df_name, new_col_name)
            code = f"{new_column}\n{grouping}"
            return code
    else:
        return None


# MidasDataFrame
def get_datetime_distribution_code(col_name, df):
    col_value = df.table.column(col_name)
    for h in DATE_HIERARCHY:
        r = try_parsing_date_time_level(h, col_value, col_name, df.df_name)
        if r:
            return (r, True, "")
    return ("", False, "Cannot parse the date time column")


def get_numeric_distribution_code(current_max_bins, unique_vals, col_name, df_name, new_name, reference_name) -> Tuple[str, bool, str]:
    d_max = unique_vals[-1]
    d_min = unique_vals[0]
    min_bucket_size = (d_max - d_min) / MAX_GENERATED_BINS
    # imports = "import numpy as np"
    try:
        bound = snap_to_nice_number(min_bucket_size)
        code = create_binning_code(bound, col_name, df_name, new_name, reference_name)
        return (code, True, "")
    except InternalLogicalError as e:
        # let's still given them a stub code
        code = create_binning_code(STUB_DISTRIBUTION_BIN, col_name, df_name, new_name, reference_name)
        return (f"# Please fix the following \n{code}", False, f"We were not able to create a distribution for column {col_name}, df {df_name}, because of error: {e}.")
    

def snap_to_nice_number(n: float):
    if n == np.inf:
        raise InternalLogicalError("Should not have gotten infinity")
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


# taken from ipyvega
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
        return None
        # raise InternalLogicalError("Cannot sanitize empty df")

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
            df[col_name] = np.where(bad_values, None, col).astype(object)
            # col.astype(object)[~bad_values]= None
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
            df[col_name] = np.where(notnull(col), col, None).astype(object)
    return df

# B2DataFrame
def dataframe_to_dict(df, include_filter_label: FilterLabelOptions):
    """[summary]
    
    Keyword Arguments:
        include_filter_label {bool} -- whether we should insert another column indicating (default: {False})
    """
    clean_df = sanitize_dataframe(df.table)
    if clean_df is None:
        return []

    def s(x):
        k = {}
        for i, v in enumerate(x):
            k[clean_df.labels[i]] = v
        if include_filter_label != FilterLabelOptions.none:
            k[IS_OVERVIEW_FIELD_NAME] = include_filter_label.value
        return k
    return list(map(s, clean_df.rows))
