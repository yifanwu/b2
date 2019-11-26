from typing import Optional
from pandas import DataFrame

from midas.defaults import CHART_HEIGHT, CHART_WIDTH, Y_DOMAIN_SIGNAL, CHART_WIDTH_SIGNAL, CHART_HEIGHT_SIGNAL, X_DOMAIN_SIGNAL
from midas.vis_types import VegaSpecType

# def gen_x_domain_signals():
#     # assume that this is not categorical
#     return [{
#         "name": X_DOMAIN_SIGNAL,
#         "value": 0
#     }
#     # {
#     #     "name": X_DOMAIN_BY_DATA_SIGNAL,
#     #     "value": "null"
#     # }
#     ]

def gen_domain_signals():
    return [{
        "name": Y_DOMAIN_SIGNAL,
        "value": 0
    },
    {
        "name": X_DOMAIN_SIGNAL,
        "value": 0
    }
    ]


def gen_width_height_signals():
    return [
        {
            "name": CHART_WIDTH_SIGNAL,
            "value": CHART_WIDTH,
            "on": [
                {
                    "events": { "source": "window", "type": "resize" },
                    "update": "containerSize()[0]" 
                }
            ] 
        },
        {
            "name": CHART_HEIGHT_SIGNAL,
            "value": CHART_HEIGHT,
            "on": [
                {
                    "events": { "source": "window", "type": "resize" },
                    "update": "containerSize()[1]" 
                }
            ] 
        }
    ]


def gen_spec_base(config=None) -> VegaSpecType:
    # commented out the following which can change label orientation
    has_angle = (config is None) or ("label_angle" not in config)
    labelAngle = 0 if has_angle else config["label_angle"]
    base = {
            "$schema": "https://vega.github.io/schema/vega/v5.json",
            "width": CHART_WIDTH,
            "height": CHART_HEIGHT,
            "padding": 5,
            "config": {
                "axisX": {
                    "labelAngle": labelAngle,
                }
            }
        }
    return base

