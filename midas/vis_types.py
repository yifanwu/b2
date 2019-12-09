from datetime import datetime
from enum import Enum
from typing import NamedTuple, List, Any, Optional, Dict

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



class DfTransformType(Enum):
    categorical_distribution = "categorical_distribution"
    numeric_distribution = "numeric_distribution"

class DfTransform(object):
    df_transform_type: DfTransformType
    pass

class NumericDistribution(DfTransform):
    def __init__(self):
        self.df_transform_type = DfTransformType.numeric_distribution
        self.bins = None

    def set_bin(self, bins):
        self.bins = bins


class CategoricalDistribution(DfTransform):
    def __init__(self):
        self.df_transform_type = DfTransformType.categorical_distribution


# basic stub for Vega typing
VegaSpecType = Dict[str, Any]

class EncodingSpec(object):
    def __init__(self, shape: str, x: str, y: str):
        # bar, circle, line
        self.shape = shape
        self.x = x
        self.y = y

    def __eq__(self, other: 'EncodingSpec'):
        return self.shape == other.shape and self.x == other.x and self.y == other.y

    def __ne__(self, other: 'EncodingSpec'):
        return not self.__eq__(other)
    
    def __repr__(self):
        return f"EncodingSpec({self.shape!r}, {self.x!r}, {self.y!r})"

    def to_json(self):
        return '{{"shape": "{0}", "x": "{1}", "y" : "{2}"}}'.format(self.shape, self.x, self.y)

# class ChartInfo(NamedTuple):
#     """[summary]
    
#     Arguments:
#         NamedTuple {[type]} -- [description]
#     """
#     chart_type: ChartType
#     # ASK Arvind: this seems to be redundant information to the vega spec?
#     encodings: Dict[Channel, str]
#     vega_spec: VegaSpecType
#     chart_title: str
