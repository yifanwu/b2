
from pandas import DataFrame

from .defaults import DEFAULT_DATA_SOURCE, X_SCALE, Y_SCALE
from .shared_all import gen_spec_base
from .shared_one_dim import gen_x_brush_signal, gen_x_brush_mark
from .data_processing import sanitize_dataframe

# note that if we don't specify, it's automatically inferred
# :%Y-%m-%d
def gen_linechart_spec(x_field: str, y_field: str, data: DataFrame, date_format:str=""):
    # spec_base = gen_scatterplot_spec(x_field, y_field, data)
    spec_base = gen_spec_base()
    # line chart need special spec because it needs the time
    sanitzied_df = sanitize_dataframe(data)
    spec_base["data"] = [{
        "name": DEFAULT_DATA_SOURCE,
        "values": sanitzied_df.to_dict(orient='records'),
        "format":{
            "parse": {
                x_field: f"date{date_format}"
            }
        },
        "transform": [{
            "type": "collect",
            "sort": {"field": x_field}
        }]
    }]

    # then add lines
    spec_base["scales"] = [
        {
            "name": X_SCALE,
            "type": "time",
            "domain": {"data": DEFAULT_DATA_SOURCE, "field": x_field},
            "range": "width"
        },
        {
            "name": Y_SCALE,
            "type": "linear",
            "round": True,
            "nice": True,
            "zero": True,
            "domain": {"data": DEFAULT_DATA_SOURCE, "field": y_field},
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
            "from": {"data": DEFAULT_DATA_SOURCE},
            "encode": {
                "enter": {
                    "x": {"scale": X_SCALE, "field": x_field},
                    "y": {"scale": Y_SCALE, "field": y_field},
                    "strokeWidth": {"value": 2}
                }
            },
        },
        brush_mark
    ]
    spec_base["signals"] = gen_x_brush_signal()
    return spec_base