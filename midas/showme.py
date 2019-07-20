"""very simple visualizations
   cases covered:
   * single attribute, get distribution
   * two attributes, bar, scatter, or line
"""
from typing import Optional, Dict
from pandas import Dataframe, Series, cut
from pandas.api.types import is_string_dtype, is_numeric_dtype, is_boolean_dtype

# all data sources we will assume to be DEFAULT_DATA_SOURCE
DEFAULT_DATA_SOURCE = "table"
COUNT_COL_NAME = "count"
X_PIXEL_SIGNAL = "xBrushPixel"
X_SELECT_SIGNAL = "xBrush"
Y_PIXEL_SIGNAL = "xBrushPixel"
Y_SELECT_SIGNAL = "yBrush"
CHART_HEIGHT = 200
CHART_WIDTH = 400

def gen_click_signal():
    return {
        "name": "click",
        "value": {},
        "on": [
            {"events": "rect:click", "update": "datum"}
        ]
    }

def gen_x_brush_signal():
    return [
        {
          "name": "xBrushPixel",
          "value": [0, 0],
          "on": [
            {
              "events": "@overview:mousedown",
              "update": "[x(), x()]"
            },
            {
              "events": "[@overview:mousedown, window:mouseup] > window:mousemove!",
              "update": "[brush[0], clamp(x(), 0, width)]"
            },
            {
              "events": {"signal": "delta"},
              "update": "clampRange([anchor[0] + delta, anchor[1] + delta], 0, width)"
            }
          ]
        },
        {
          "name": "xanchor",
          "value": None,
          "on": [{"events": "@brush:mousedown", "update": "slice(brush)"}]
        },
        {
          "name": "xdown",
          "value": 0,
          "on": [{"events": "@brush:mousedown", "update": "x()"}]
        },
        {
          "name": "delta",
          "value": 0,
          "on": [
            {
              "events": "[@brush:mousedown, window:mouseup] > window:mousemove!",
              "update": "x() - xdown"
            }
          ]
        },
        {
          "name": X_SELECT_SIGNAL,
          "push": "outer",
          "on": [
            {
              "events": {"signal": "xBrushPixel"},
              "update": "span(brush) ? invert('xOverview', brush) : null"
            }
          ]
        }]


def gen_scatterplot_spec(spec_base: Dict, x_field: str, y_field: str, data_name: Optional[str] = None):
    data_name = DEFAULT_DATA_SOURCE if (data_name == None) else data_name
    spec_base["scales"] = [
        {
            "name": "x",
            "type": "linear",
            "round": True,
            "nice": True,
            "zero": True,
            "domain": {"data": data_name, "field": x_field},
            "range": "width"
        },
        {
            "name": "y",
            "type": "linear",
            "round": True,
            "nice": True,
            "zero": True,
            "domain": {"data": data_name, "field": y_field},
            "range": "height"
        }
    ]
    spec_base["axes"]: [
        {
            "scale": "x",
            "grid": True,
            "domain": False,
            "orient": "bottom",
            "tickCount": 5,
            "title": x_field
        },
        {
            "scale": "y",
            "grid": True,
            "domain": False,
            "orient": "left",
            "titlePadding": 5,
            "title": y_field
        }
    ]
    spec_base["marks"]: [
        {
            "name": "marks",
            "type": "symbol",
            "from": {"data": data_name},
            "encode": {
                "update": {
                "x": {"scale": "x", "field": x_field},
                "y": {"scale": "y", "field": y_field},
                "size": {"value": 4},
                "shape": {"value": "circle"},
                "strokeWidth": {"value": 2},
                "opacity": {"value": 0.5},
                "stroke": {"value": "#4682b4"},
                "fill": {"value": "transparent"}
                }
            }
        },
    ]
    return spec_base


def set_bar_chart_spec(spec_base: Dict, x_field: str, y_field: str, data_name: Optional[str] = None):
    data_name = DEFAULT_DATA_SOURCE if (data_name == None) else data_name
    spec_base["scales"] = [
        {
            "name": "xscale",
            "type": "band",
            "domain": {"data": data_name, "field": x_field},
            "range": "width",
            "padding": 0.05,
            "round": True
        },
        {
            "name": "yscale",
            "domain": {"data": data_name, "field": y_field},
            "nice": True,
            "range": "height"
        }
    ]
    # note that the update logic is included here since they are all the same
    spec_base["marks"] = [
        {
            "type": "rect",
            "from": {"data": data_name},
            "encode": {
                "enter": {
                    "x": {"scale": "xscale", "field": x_field},
                    "width": {"scale": "xscale", "band": 1},
                    "y": {"scale": "yscale", "field": y_field},
                    "y2": {"scale": "yscale", "value": 0}
                },
                "update": {
                    "fill":  [{"test": "datum === tooltip", "value": "green"}, {"value": "steelblue"}]
                }
            }
        },
        {
          "type": "rect",
          "name": "xBrushMark",
          "encode": {
            "enter": {
              "y": {"value": 0},
              "height": {"value": CHART_HEIGHT},
              "fill": {"value": "#333"},
              "fillOpacity": {"value": 0.2}
            },
            "update": {
              "x": {"signal": f"{X_PIXEL_SIGNAL}[0]"},
              "x2": {"signal": f"{X_PIXEL_SIGNAL}[1]"}
            }
          }
        },
    ]
    spec_base["signal"] = gen_x_brush_signal()
    return spec_base


def gen_spec_base():
    return {
            "$schema": "https://vega.github.io/schema/vega/v5.json",
            "width": CHART_WIDTH,
            "height": CHART_HEIGHT,
            "padding": 5,
        }

def set_data_attr(spec_base: Dict, data: Dataframe) -> Dict:
    """set_data_attr takes the df and transformes it into Dict object shape for serialization
    
    Arguments:
        spec_base {Dict} -- [description]
        data {Dataframe} -- [description]
    
    Returns:
        Dict -- [description]
    """
    spec_base["data"] = {
        "name": DEFAULT_DATA_SOURCE,
        "values": data.to_dict(orient='records')
    }
    return spec_base

def get_categorical_districution(data: Series) -> Dataframe:
    # just select the top 10
    return data.value_counts().to_frame(COUNT_COL_NAME)

def get_numeric_districution(data: Series) -> Dataframe:
    # wow can just use pd.cut
    return cut(data, bins=10).value_counts().to_frame(COUNT_COL_NAME)

def gen_spec(df: Dataframe):
    """Implements basic show me like feature
      if there is only one column, try to do a distribution with reasonable binning
      if one categorical, one numeric, barchart
      if two numeric, scatter, unless if one is time, then line (line, todo)
    """
    # error if df has no column
    df_len = len(df.columns)
    df_to_visualize: Dataframe = None
    spec_base = gen_spec_base()
    if (df_len == 0):
        raise Exception("Dataframe has too few columns")
    elif (df_len == 1):
        first_col = df.columns.values[0]
        if (is_string_dtype(df[first_col])):
            df_to_visualize = get_categorical_districution(df[first_col])
        else:
            df_to_visualize = get_numeric_districution(df[first_col])
        # then generated the bar chart
        spec_base = set_data_attr(spec_base, df_to_visualize)
        return set_bar_chart_spec(spec_base, first_col, COUNT_COL_NAME)
    else:
        # fow now let's just take the frist two columns
        second_col = df.columns.values[1]
        spec_base = set_data_attr(spec_base, df[df[first_col, second_col]])
        if (is_string_dtype(df[first_col]) & is_numeric_dtype(df[second_col])):
            return set_bar_chart_spec(spec_base, first_col, second_col)
        elif (is_numeric_dtype(df[first_col]) & is_string_dtype(df[second_col])):
            return set_bar_chart_spec(spec_base, second_col, first_col)
        elif (is_numeric_dtype(df[first_col]) & is_numeric_dtype(df[second_col])):
            return gen_scatterplot_spec(spec_base, first_col, second_col)
