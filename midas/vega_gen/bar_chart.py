
from typing import Optional, Dict
from pandas import DataFrame

from .defaults import DEFAULT_DATA_SOURCE, X_SCALE, X_PIXEL_SIGNAL, Y_SCALE, CHART_HEIGHT, BRUSH_MARK
from .shared_one_dim import gen_x_brush_signal, gen_x_brush_mark
from .shared_all import gen_spec_base

from .defaults import SELECTION_SIGNAL

def gen_bar_chart_spec(x_field: str, y_field: str, data: DataFrame):
    spec_base = gen_spec_base(data)
    spec_base["scales"] = [
        {
            "name": X_SCALE,
            "type": "band",
            "domain": {"data": DEFAULT_DATA_SOURCE, "field": x_field},
            "range": "width",
            "padding": 0.05,
            "round": True
        },
        {
            "name": Y_SCALE,
            "domain": {"data": DEFAULT_DATA_SOURCE, "field": y_field},
            "nice": True,
            "range": "height"
        }
    ]
    # note that the update logic is included here since they are all the same
    spec_base["marks"] = [
        {
            "type": "rect",
            "from": {"data": DEFAULT_DATA_SOURCE},
            "encode": {
                "enter": {
                    "x": {"scale": X_SCALE, "field": x_field},
                    "width": {"scale": X_SCALE, "band": 1},
                    "y": {"scale": Y_SCALE, "field": y_field},
                    "y2": {"scale": Y_SCALE, "value": 0}
                },
                "update": {
                    "fill": [
                        {
                            "test": f"{SELECTION_SIGNAL} ? indexof({SELECTION_SIGNAL}.x, datum.{x_field}) > -1 : false",
                            "value": "red"
                        },
                        {"value": "blue"
                    }]
                }
            }
        },
        gen_x_brush_mark()
    ]
    spec_base["axes"] = [
        { "orient": "bottom", "scale": X_SCALE },
        { "orient": "left", "scale": Y_SCALE }
    ]

    spec_base["signals"] = gen_x_brush_signal()
    return spec_base
