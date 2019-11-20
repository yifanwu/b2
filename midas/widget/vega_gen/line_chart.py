
from pandas import DataFrame

from midas.defaults import FILTERED_DATA_SOURCE, X_SCALE, Y_SCALE, Y_DOMAIN_SIGNAL, Y_DOMAIN_BY_DATA_SIGNAL, X_DOMAIN_BY_DATA_SIGNAL, X_DOMAIN_SIGNAL, BASE_DATA_SOURCE
from .shared_all import gen_spec_base
from .shared_one_dim import gen_x_brush_signal, gen_x_brush_mark
from .shared_all import gen_spec_base, gen_domain_signals, gen_width_height_signals

# note that if we don't specify, it's automatically inferred
# :%Y-%m-%d
def gen_linechart_spec(x_field: str, y_field: str, date_format: str=""):
    # spec_base = gen_scatterplot_spec(x_field, y_field, data)
    spec_base = gen_spec_base()
    # line chart need special spec because it needs the time
    spec_base["data"] = [{
            "name": FILTERED_DATA_SOURCE,
            "values": []
        },{
            "name": BASE_DATA_SOURCE,
            "values": [],
            "format":{
                "parse": {
                    x_field: f"date{date_format}"
                }
            },
            "transform": [
                {
                    "type": "collect",
                    "sort": {"field": x_field}
                },
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
        }
    ]

    # then add lines
    spec_base["scales"] = [
        {
            "name": X_SCALE,
            "type": "time",
            "zero": False,
            # "domain": {"data": DEFAULT_DATA_SOURCE, "field": x_field},
            "domain": {"signal": f"{X_DOMAIN_SIGNAL} ? {X_DOMAIN_SIGNAL} : {X_DOMAIN_BY_DATA_SIGNAL}"},
            "range": "width"
        },
        {
            "name": Y_SCALE,
            "type": "linear",
            "round": True,
            "nice": True,
            "zero": False,
            # "domain": {"data": DEFAULT_DATA_SOURCE, "field": y_field},
            "domain": {"signal": f"{Y_DOMAIN_SIGNAL} ? {Y_DOMAIN_SIGNAL} : {Y_DOMAIN_BY_DATA_SIGNAL}"},
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
    brush_mark = gen_x_brush_mark()
    spec_base["marks"]= [
        {
            "type": "line",
            "from": {"data": BASE_DATA_SOURCE},
            "encode": {
                "enter": {
                    "x": {"scale": X_SCALE, "field": x_field},
                    "y": {"scale": Y_SCALE, "field": y_field},
                    "strokeWidth": {"value": 2},
                    "stroke": "#ccc"
                }
            },
        },
        {
            "type": "line",
            "from": {"data": FILTERED_DATA_SOURCE},
            "encode": {
                "enter": {
                    "x": {"scale": X_SCALE, "field": x_field},
                    "y": {"scale": Y_SCALE, "field": y_field},
                    "strokeWidth": {"value": 2},
                    "stroke": "steelblue"
                }
            },
        },
        brush_mark
    ]
    spec_base["signals"] = gen_width_height_signals() + \
         gen_x_brush_signal() + \
        gen_domain_signals()
    
    return spec_base