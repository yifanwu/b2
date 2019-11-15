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


class DfTransform(Enum):
    categorical_distribution = "categorical_distribution"
    numeric_distribution = "numeric_distribution"


# basic stub for Vega typing
VegaSpecType = Dict[str, Any]


class ChartInfo(NamedTuple):
    """[summary]
    
    Arguments:
        NamedTuple {[type]} -- [description]
    """
    chart_type: ChartType
    # ASK Arvind: this seems to be redundant information to the vega spec?
    encodings: Dict[Channel, str]
    vega_spec: VegaSpecType
    chart_title: str
    additional_transforms: Optional[DfTransform]

