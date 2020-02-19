from datetime import datetime
from enum import Enum
from typing import List, Any, Dict

from midas.midas_algebra.selection import SelectionValue
from midas.state_types import DFName
from midas.util.utils import get_random_string

class ChartType(Enum):
    bar_categorical = "bar_categorical"
    bar_linear = "bar_linear"
    scatter = "scatter"
    line = "line"


# set to numerical values to save space.
class FilterLabelOptions(Enum):
    filtered=False
    unfiltered=True
    none=2


class Channel(Enum):
    x = "x"
    y = "y"
    color = "color"


class SelectionEvent(object):
    def __init__(self, interaction_time: datetime, predicate: List[SelectionValue], df_name: DFName):
        self.interaction_time = interaction_time
        self.predicate = predicate
        self.df_name = df_name
        self.id = get_random_string(5)

    def __repr__(self):
        return f"df: {self.df_name}\n  predicates: {self.predicate}"


# basic stub for Vega typing
VegaSpecType = Dict[str, Any]

ENCODING_COUNT = 7

class EncodingSpec(object):
    def __init__(self, mark: str, x: str, x_type: str, y: str, y_type: str, selection_type: str, selection_dimensions: str):
        self.mark = mark # bar, circle, line
        self.x = x
        self.x_type = x_type
        self.y = y
        self.y_type = y_type
        self.selection_dimensions = selection_dimensions
        self.selection_type = selection_type


    def __eq__(self, other: 'EncodingSpec'):
        return self.to_json() == other.to_json()


    def __ne__(self, other: 'EncodingSpec'):
        return not self.__eq__(other)
    

    def __repr__(self):
        # FIXME: not sure why we have a "!r" here...
        return f"EncodingSpec({self.mark!r}, {self.x!r}, {self.x_type}, {self.y!r}, {self.y_type}, {self.selection_dimensions}, {self.selection_type!r})"


    def to_json(self):
        return f'{{"mark": "{self.mark}", "x": "{self.x}", "xType": "{self.x_type}", "y": "{self.y}", "yType": "{self.y_type}", "selectionDimensions": "{self.selection_dimensions}", "selectionType": "{self.selection_type}"}}'
