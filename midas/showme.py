"""very simple visualizations
cases covered:
* single attribute, get distribution
* two attributes, bar, scatter, or line
"""
from pandas import DataFrame
from pandas.api.types import is_string_dtype, is_numeric_dtype, is_bool_dtype

from .errors import type_check_with_warning
from .vega_gen.bar_chart import set_bar_chart_spec
from .vega_gen.scatter_plot import gen_scatterplot_spec
from .vega_gen.shared_all import gen_spec_base
from .vega_gen.data_processing import get_categorical_distribution, \
    get_numeric_distribution, set_data_attr
from .vega_gen.defaults import COUNT_COL_NAME


def gen_spec(df: DataFrame):
    """Implements basic show me like feature
        if there is only one column, try to do a distribution with reasonable binning
        if one categorical, one numeric, barchart
        if two numeric, scatter, unless if one is time, then line (line, todo)

    TODO:
    [ ] if the numeric value has a limited number of unique values, treat as bar chart!
    """
    type_check_with_warning(df, DataFrame)
    # error if df has no column
    df_len = len(df.columns)
    df_to_visualize: DataFrame = None
    spec_base = gen_spec_base()
    if (df_len == 0):
        raise Exception("DataFrame has too few columns")
    elif (df_len == 1):
        first_col = df.columns.values[0]
        if (is_string_dtype(df[first_col])):
            df_to_visualize = get_categorical_distribution(df[first_col], first_col)
        else:
            df_to_visualize = get_numeric_distribution(df[first_col], first_col)
        # then generated the bar chart
        spec_base = set_data_attr(spec_base, df_to_visualize)
        return set_bar_chart_spec(spec_base, first_col, COUNT_COL_NAME)
    else:
        first_col = df.columns.values[0]
        # fow now let's just take the frist two columns
        second_col = df.columns.values[1]
        spec_base = set_data_attr(spec_base, df[[first_col, second_col]])
        if (is_string_dtype(df[first_col]) & is_numeric_dtype(df[second_col])):
            return set_bar_chart_spec(spec_base, first_col, second_col)
        elif (is_numeric_dtype(df[first_col]) & is_string_dtype(df[second_col])):
            return set_bar_chart_spec(spec_base, second_col, first_col)
        elif (is_numeric_dtype(df[first_col]) & is_numeric_dtype(df[second_col])):
            s = gen_scatterplot_spec(spec_base, first_col, second_col)
            s["config"] = {
                "axisX": {
                    "labelAngle": 45,
                }
            }
            return s

