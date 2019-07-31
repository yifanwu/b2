"""very simple visualizations
   cases covered:
   * single attribute, get distribution
   * two attributes, bar, scatter, or line
"""
from typing import Optional, Dict
from pandas import DataFrame, Series, cut
from pandas.api.types import is_string_dtype, is_numeric_dtype, is_bool_dtype

from .errors import type_check_with_warning
from .serialization import sanitize_dataframe
from .defaults import DEFAULT_DATA_SOURCE, COUNT_COL_NAME, X_PIXEL_SIGNAL, X_SELECT_SIGNAL, Y_PIXEL_SIGNAL, Y_SELECT_SIGNAL, CHART_HEIGHT, CHART_INNER_HEIGHT, CHART_WIDTH, CHART_INNER_WIDTH, SELECTION_SIGNAL, X_SCALE, Y_SCALE

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
          "name": X_PIXEL_SIGNAL,
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
              "events": {"signal": f"{X_PIXEL_SIGNAL}"},
              "update": f"span({X_PIXEL_SIGNAL}) ? invert(\"{X_SCALE}\", {X_PIXEL_SIGNAL}) : null"
            }
          ]
        }]


def gen_scatterplot_spec(spec_base: Dict, x_field: str, y_field: str, data_name: Optional[str] = None):
    data_name = DEFAULT_DATA_SOURCE if (data_name == None) else data_name
    spec_base["scales"] = [
        {
            "name": X_SCALE,
            "type": "linear",
            "round": True,
            "nice": True,
            "zero": True,
            "domain": {"data": data_name, "field": x_field},
            "range": "width"
        },
        {
            "name": Y_SCALE,
            "type": "linear",
            "round": True,
            "nice": True,
            "zero": True,
            "domain": {"data": data_name, "field": y_field},
            "range": "height"
        }
    ]
    spec_base["axes"] = [
        {
            "scale": X_SCALE,
            "grid": True,
            "domain": False,
            "orient": "bottom",
            "tickCount": 5,
            "title": x_field
        },
        {
            "scale": Y_SCALE,
            "grid": True,
            "domain": False,
            "orient": "left",
            "titlePadding": 5,
            "title": y_field
        }
    ]
    spec_base["marks"] = [
        {
            "name": "marks",
            "type": "symbol",
            "from": {"data": data_name},
            "encode": {
                "update": {
                "x": {"scale": X_SCALE, "field": x_field},
                "y": {"scale": Y_SCALE, "field": y_field},
                "size": {"value": 4},
                "shape": {"value": "circle"},
                "strokeWidth": {"value": 5},
                "opacity": {"value": 0.5},
                "stroke": {"value": "#4682b4"},
                "fill": {"value": "transparent"}
                }
            }
        },
        {
          "type": "rect",
          "name": "brush",
          "encode": {
            "enter": {
              "fill": {"value": "#333"},
              "fillOpacity": {"value": 0.2}
            },
            "update": {
              "x": {"signal": f"{X_PIXEL_SIGNAL} ? {X_PIXEL_SIGNAL}[0] : 0"},
              "x2": {"signal": f"{X_PIXEL_SIGNAL} ? {X_PIXEL_SIGNAL}[1] : 0"},
              "y": {"signal": f"{Y_PIXEL_SIGNAL} ?  {Y_PIXEL_SIGNAL}[0] : 0"},
              "y2": {"signal": f"{Y_PIXEL_SIGNAL} ? {Y_PIXEL_SIGNAL}[1] : 0"}
            }
          }
    }
    ]
    spec_base["signals"] = [
        { "name": "chartWidth", "value": CHART_INNER_WIDTH },
        { "name": "chartHeight", "value": CHART_INNER_HEIGHT },
        {
          "name": SELECTION_SIGNAL,
          "on": [
            {
              "events": {"signal": f"{X_PIXEL_SIGNAL} || {Y_PIXEL_SIGNAL}"},
              "update": f"(span({X_PIXEL_SIGNAL}) || span({Y_PIXEL_SIGNAL})) ? {{x: invert('{X_SCALE}', {X_PIXEL_SIGNAL}), y: invert('{Y_SCALE}', {Y_PIXEL_SIGNAL})}} : null"
            }
          ]
        },
        {
        "name": X_PIXEL_SIGNAL,
        "value": 0,
        "on": [
          {
            "events": "mousedown",
            "update": "[x(), x()]"
          },
          {
            "events": "[mousedown, mouseup] > mousemove",
            "update": f"[{X_PIXEL_SIGNAL}[0], clamp(x(), 0, chartWidth)]"
          },
          {
            "events": {"signal": "delta"},
            "update": "clampRange([anchorX[0] + delta[0], anchorX[1] + delta[0]], 0, chartWidth)"
          }
        ]
      },
      {
        "name": Y_PIXEL_SIGNAL,
        "value": 0,
        "on": [
          {
            "events": "mousedown",
            "update": "[y(), y()]"
          },
          {
            "events": "[mousedown, mouseup] > mousemove",
            "update": f"[{Y_PIXEL_SIGNAL}[0], clamp(y(), 0, chartHeight)]"
          },
          {
            "events": {"signal": "delta"},
            "update": "clampRange([anchorY[0] + delta[1], anchorY[1] + delta[1]], 0, chartHeight)"
          }
        ]
      },
      {
        "name": "down", "value": [0, 0],
        "on": [{"events": "@brush:mousedown", "update": "[x(), y()]"}]
      },
      {
        "name": "anchorX", "value": 0,
        "on": [{"events": "@brush:mousedown", "update": f"slice({X_PIXEL_SIGNAL})"}]
      },
      {
        "name": "anchorY", "value": 0,
        "on": [{"events": "@brush:mousedown", "update": f"slice({Y_PIXEL_SIGNAL})"}]
      },
      {
        "name": "delta", "value": [0, 0],
        "on": [
          {
            "events": "[@brush:mousedown, window:mouseup] > window:mousemove",
            "update": "[x() - down[0], y() - down[1]]"
          }
        ]
      }
    ]
    return spec_base


def set_bar_chart_spec(spec_base: Dict, x_field: str, y_field: str, data_name: Optional[str] = None):
    data_name = DEFAULT_DATA_SOURCE if (data_name == None) else data_name
    spec_base["scales"] = [
        {
            "name": X_SCALE,
            "type": "band",
            "domain": {"data": data_name, "field": x_field},
            "range": "width",
            "padding": 0.05,
            "round": True
        },
        {
            "name": Y_SCALE,
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
                    "x": {"scale": X_SCALE, "field": x_field},
                    "width": {"scale": X_SCALE, "band": 1},
                    "y": {"scale": "yscale", "field": y_field},
                    "y2": {"scale": "yscale", "value": 0}
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


def set_data_attr(spec_base: Dict, data: DataFrame) -> Dict:
    """set_data_attr takes the df and transformes it into Dict object shape for serialization
    
    Arguments:
        spec_base {Dict} -- [description]
        data {DataFrame} -- [description]
    
    Returns:
        Dict -- [description]
    """
    sanitzied_df = sanitize_dataframe(data)
    spec_base["data"] = [{
        "name": DEFAULT_DATA_SOURCE,
        "values": sanitzied_df.to_dict(orient='records')
    }]
    return spec_base


def get_categorical_districution(data: Series) -> DataFrame:
    # just select the top 10
    return data.value_counts().to_frame(COUNT_COL_NAME)


def get_numeric_districution(data: Series) -> DataFrame:
    # wow can just use pd.cut
    return cut(data, bins=10).value_counts().to_frame(COUNT_COL_NAME)


def gen_spec(df: DataFrame):
    """Implements basic show me like feature
      if there is only one column, try to do a distribution with reasonable binning
      if one categorical, one numeric, barchart
      if two numeric, scatter, unless if one is time, then line (line, todo)
      TODO:
      [ ] if the numeric value has a limited number of unique values, also treat as bar chart!
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
            df_to_visualize = get_categorical_districution(df[first_col])
        else:
            df_to_visualize = get_numeric_districution(df[first_col])
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
            return gen_scatterplot_spec(spec_base, first_col, second_col)
