"""very simple visualizations
cases covered:
* single attribute, get distribution
* two attributes, bar, scatter, or line
"""
from typing import Optional, Dict
from datascience.tables import Table
from pandas.api.types import is_string_dtype, is_numeric_dtype, is_datetime64_any_dtype 

from .vega_gen.bar_chart import gen_bar_chart_spec
from .vega_gen.scatter_plot import gen_scatterplot_spec
from .vega_gen.line_chart import gen_linechart_spec

from midas.constants import COUNT_COL_NAME
from midas.util.errors import type_check_with_warning, InternalLogicalError
from midas.vis_types import ChartInfo, ChartType, Channel, DfTransform, NumericDistribution, CategoricalDistribution

def gen_spec(df: Table, df_name: str, config) -> Optional[ChartInfo]:
    """Implements basic show me like feature
        if there is only one column, try to do a distribution with reasonable binning
        if one categorical, one numeric, barchart
        if two numeric, scatter, unless if one is time, then line (line, todo)

    TODO:
    [ ] if the numeric value has a limited number of unique values, treat as bar chart!
    [ ] also add line chart
    """
    type_check_with_warning(df, Table)
    # error if df has no column
    df_len = len(df.columns)
    chart_type: Optional[ChartType] = None
    encoding: Optional[Dict[Channel, str]] = None
    additional_transforms: Optional[DfTransform] = None
    if (df_len == 0):
        raise Exception("DataFrame has too few columns")
    elif (df_len == 1):
        first_col = df.labels[0]
        if (is_string_dtype(df[first_col])):
            additional_transforms = CategoricalDistribution()
            chart_type = ChartType.bar_categorical
        elif (is_datetime64_any_dtype(df[first_col])):
            additional_transforms = NumericDistribution()
            chart_type = ChartType.line
        else:
            additional_transforms = NumericDistribution()
            chart_type = ChartType.bar_linear
        encoding = {
            Channel.x: first_col,
            Channel.y: COUNT_COL_NAME
        }
    else:
        first_col = df.labels[0]
        # fow now let's just take the frist two columns
        second_col = df.labels[1]
        # df_to_visualize = df[[first_col, second_col]]
        if (is_string_dtype(df[first_col]) & is_numeric_dtype(df[second_col])):
            chart_type = ChartType.bar_categorical
            encoding = {
                Channel.x: first_col,
                Channel.y: second_col
            }
        elif (is_numeric_dtype(df[first_col]) & is_string_dtype(df[second_col])):
            chart_type = ChartType.bar_categorical
            encoding = {
                Channel.x: second_col,
                Channel.y: first_col
            }
        elif (is_numeric_dtype(df[first_col]) & is_numeric_dtype(df[second_col])):
            chart_type = ChartType.scatter
            encoding = {
                Channel.x: first_col,
                Channel.y: second_col
            }
            
    if chart_type:
        if encoding:
            if (chart_type == ChartType.bar_linear) or (chart_type == ChartType.bar_categorical):
                vega_spec = gen_bar_chart_spec(encoding[Channel.x], encoding[Channel.y], df_name)
            elif (chart_type == ChartType.scatter):
                vega_spec = gen_scatterplot_spec(encoding[Channel.x],
                    encoding[Channel.y], df_name)
            else:
                vega_spec = gen_linechart_spec(encoding[Channel.x],
                    encoding[Channel.y], df_name)
            return ChartInfo(chart_type, encoding, vega_spec, df_name,
            additional_transforms)

    raise InternalLogicalError(f"Failed to generate spec:\nchart_type {chart_type}\nencoding: {encoding}")
