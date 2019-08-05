from typing import Optional
from pandas import DataFrame

from .defaults import CHART_HEIGHT, CHART_WIDTH
from .data_processing import set_data_attr
from ..types import VegaSpecType

def gen_spec_base(data: Optional[DataFrame]=None) -> VegaSpecType:
    base = {
            "$schema": "https://vega.github.io/schema/vega/v5.json",
            "width": CHART_WIDTH,
            "height": CHART_HEIGHT,
            "padding": 5,
        }
    if data is not None:
        set_data_attr(base, data)
    return base
