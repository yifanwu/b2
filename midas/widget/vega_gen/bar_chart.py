from midas.defaults import DEFAULT_DATA_SOURCE, X_SCALE, Y_SCALE, Y_DOMAIN_SIGNAL, Y_DOMAIN_BY_DATA_SIGNAL, X_DOMAIN_BY_DATA_SIGNAL, X_DOMAIN_SIGNAL
from .shared_one_dim import gen_x_brush_signal, gen_x_brush_mark
from .shared_all import gen_spec_base, gen_y_domain_signals, gen_width_height_signals
from midas.defaults import SELECTION_SIGNAL

def gen_bar_chart_spec(x_field: str, y_field: str):
    spec_base = gen_spec_base()
    spec_base["data"] = [{
        "name": DEFAULT_DATA_SOURCE,
        "values": [],
        "transform": [
            {
                "type": "extent",
                "field": y_field,
                "signal": Y_DOMAIN_BY_DATA_SIGNAL
            },
            {
                "type": "extent",
                "field": x_field,
                "signal": X_DOMAIN_BY_DATA_SIGNAL
            }
        ]
    }]
    spec_base["scales"] = [
        {
            "name": X_SCALE,
            "type": "band",
            # "domain": {"data": DEFAULT_DATA_SOURCE, "field": x_field},
            "domain": {"signal": f"{X_DOMAIN_SIGNAL} ? {X_DOMAIN_SIGNAL} : {X_DOMAIN_BY_DATA_SIGNAL}"},
            "range": "width",
            "padding": 0.05,
            "round": True
        },
        {
            "name": Y_SCALE,
            # "domain": {"data": DEFAULT_DATA_SOURCE, "field": y_field},
            "domain": {"signal": f"{Y_DOMAIN_SIGNAL} ? {Y_DOMAIN_SIGNAL} : {Y_DOMAIN_BY_DATA_SIGNAL}"},
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

    spec_base["signals"] = gen_width_height_signals() + \
        gen_x_brush_signal() + gen_y_domain_signals()
    return spec_base
