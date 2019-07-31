
from typing import Optional, Dict
from .defaults import DEFAULT_DATA_SOURCE, X_SCALE, X_PIXEL_SIGNAL, Y_SCALE, CHART_HEIGHT, BRUSH_MARK

from .shared_one_dim import gen_x_brush_signal  

from .defaults import X_SELECT_SIGNAL

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
                    "y": {"scale": Y_SCALE, "field": y_field},
                    "y2": {"scale": Y_SCALE, "value": 0}
                },
                "update": {
                    "fill": [
                        {
                            "test": f"{X_SELECT_SIGNAL} ? indexof({X_SELECT_SIGNAL}, datum.{x_field}) > -1 : false",
                            "value": "red"
                        },
                        {"value": "blue"
                    }]
                }
            }
        },
        {
            "type": "rect",
            "name": BRUSH_MARK,
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
    spec_base["axes"] = [
        { "orient": "bottom", "scale": X_SCALE },
        { "orient": "left", "scale": Y_SCALE }
    ]

    spec_base["signals"] = gen_x_brush_signal()
    return spec_base
