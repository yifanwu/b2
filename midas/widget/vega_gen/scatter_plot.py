
from typing import Optional, Dict
from pandas import DataFrame

from midas.defaults import FILTERED_DATA_SOURCE, X_SCALE, X_PIXEL_SIGNAL, Y_SCALE, Y_PIXEL_SIGNAL, SELECTION_SIGNAL, BRUSH_MARK, Y_DOMAIN_SIGNAL, Y_DOMAIN_BY_DATA_SIGNAL, X_DOMAIN_BY_DATA_SIGNAL, X_DOMAIN_SIGNAL, BASE_DATA_SOURCE
from .shared_all import gen_spec_base, gen_domain_signals, gen_width_height_signals


def gen_scatterplot_spec(spec_base, x_field: str, y_field: str):
    # spec_base = gen_spec_base()
    spec_base["data"] = [
        {
            "name": BASE_DATA_SOURCE,
            "values": []
        },
        {
        "name": FILTERED_DATA_SOURCE,
        "values": [],
        # "transform": [
        #     {
        #         "type": "extent",
        #         "field": y_field,
        #         "signal": Y_DOMAIN_BY_DATA_SIGNAL
        #     },
        #     {
        #         "type": "extent",
        #         "field": x_field,
        #         "signal": X_DOMAIN_BY_DATA_SIGNAL
        #     }
        # ]
    }]
    spec_base["scales"] = [
        {
            "name": X_SCALE,
            "type": "linear",
            "round": True,
            "nice": True,
            "zero": False,
            # "domain": {"signal": f"{X_DOMAIN_SIGNAL} ? {X_DOMAIN_SIGNAL} : {X_DOMAIN_BY_DATA_SIGNAL}"},
            "domain": {"data": BASE_DATA_SOURCE, "field": x_field},
            "range": "width"
        },
        {
            "name": Y_SCALE,
            "type": "linear",
            "round": True,
            "nice": True,
            "zero": False,
            # "domain": {"signal": f"{Y_DOMAIN_SIGNAL} ? {Y_DOMAIN_SIGNAL} : {Y_DOMAIN_BY_DATA_SIGNAL}"},
            "domain": {"data": BASE_DATA_SOURCE, "field": y_field},
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
            "from": {"data": FILTERED_DATA_SOURCE},
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
            "name": "marks",
            "type": "symbol",
            "from": {"data": BASE_DATA_SOURCE},
            "encode": {
                "update": {
                    "x": {"scale": X_SCALE, "field": x_field},
                    "y": {"scale": Y_SCALE, "field": y_field},
                    "size": {"value": 4},
                    "shape": {"value": "circle"},
                    "strokeWidth": {"value": 5},
                    "opacity": {"value": 0.5},
                    "fill": {
                        "value": "#ccc",
                        "opacity": {"value": 0.6}
                    }
                }
            }
        },
        {
            "type": "rect",
            "name": BRUSH_MARK,
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
    spec_base["signals"] = gen_width_height_signals() + \
        gen_domain_signals() + \
        [{
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
            "on": [{"events": f"@{BRUSH_MARK}:mousedown", "update": "[x(), y()]"}]
        },
        {
            "name": "anchorX", "value": 0,
            "on": [{"events": f"@{BRUSH_MARK}:mousedown", "update": f"slice({X_PIXEL_SIGNAL})"}]
        },
        {
            "name": "anchorY", "value": 0,
            "on": [{"events": f"@{BRUSH_MARK}:mousedown", "update": f"slice({Y_PIXEL_SIGNAL})"}]
        },
        {
            "name": "delta", "value": [0, 0],
            "on": [
            {
                "events": f"[@{BRUSH_MARK}:mousedown, window:mouseup] > window:mousemove",
                "update": "[x() - down[0], y() - down[1]]"
            }
            ]
        }
    ]
    return spec_base
