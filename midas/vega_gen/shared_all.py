from typing import Optional
from pandas import DataFrame

from .defaults import CHART_HEIGHT, CHART_WIDTH, Y_DOMAIN_SIGNAL, X_DOMAIN_SIGNAL, CHART_WIDTH_SIGNAL, CHART_HEIGHT_SIGNAL, X_DOMAIN_BY_DATA_SIGNAL, Y_DOMAIN_BY_DATA_SIGNAL
from .data_processing import set_data_attr
from ..types import VegaSpecType

def gen_x_domain_signals():
    # assume that this is not categorical
    return [{
        "name": X_DOMAIN_SIGNAL,
        "value": 0
    }
    # {
    #     "name": X_DOMAIN_BY_DATA_SIGNAL,
    #     "value": "null"
    # }
    ]

def gen_y_domain_signals():
    return [{
        "name": Y_DOMAIN_SIGNAL,
        "value": 0
    }
    # ,
    # {
    #     "name": Y_DOMAIN_BY_DATA_SIGNAL,
    #     "value": "null"
    # }
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


def gen_spec_base() -> VegaSpecType:
    base = {
            "$schema": "https://vega.github.io/schema/vega/v5.json",
            "width": CHART_WIDTH,
            "height": CHART_HEIGHT,
            "padding": 5,
            "config": {
                "axisX": {
                    "labelAngle": 45,
                }
            }
        }
    return base
