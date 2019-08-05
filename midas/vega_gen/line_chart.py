
from pandas import DataFrame

from .scatter_plot import gen_scatterplot_spec
from .defaults import DEFAULT_DATA_SOURCE

def gen_linechart_spec(x_field: str, y_field: str, data: DataFrame):
    spec_base = gen_scatterplot_spec(x_field, y_field, data)
    # then add lines
    spec_base["marks"].append({
        "type": "line",
        "from": {"data": DEFAULT_DATA_SOURCE},
        "encode": {
            "enter": {
                "x": {"scale": "x", "field": x_field},
                "y": {"scale": "y", "field": y_field},
                "strokeWidth": {"value": 2}
            }
        }
    })
    return spec_base