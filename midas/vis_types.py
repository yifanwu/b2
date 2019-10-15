from datetime import datetime
from enum import Enum
from typing import NamedTuple, List, Union, Any, Optional, Dict, Tuple

# hope fully no recursive imports...
from .widget.widget import MidasWidget

class ChartType(Enum):
    bar_categorical = "bar_categorical"
    bar_linear = "bar_linear"
    scatter = "scatter"
    line = "line"


class Channel(Enum):
    x = "x"
    y = "y"
    color = "color"


# hack
VegaSpecType = Dict[str, Any]


# class PredicateType(Enum):
#     one_dim_categorical = "one_dim_categorical"
#     one_dim_linear = "one_dim_linear"
#     two_dim_linear = "two_dim_linear"
    # we can add other two dim combos, but not common right now...

class TwoDimSelectionPredicate(NamedTuple):
    """
    going to assume that two dimension is both linear
    """
    interaction_time: datetime
    x_column: str
    y_column: str
    x: Tuple[float, float]
    y: Tuple[float, float]
    dimension = 2


class NullSelectionPredicate(NamedTuple):
    interaction_time: datetime
    dimension = 0


class OneDimSelectionPredicate(NamedTuple):
    interaction_time: datetime
    x_column: str
    is_categoritcal: bool
    # the first is selecting linear scale, the second categorical scale
    x: Union[Tuple[float, float], List[str]]
    dimension = 1
    

SelectionPredicate = Union[TwoDimSelectionPredicate, OneDimSelectionPredicate, NullSelectionPredicate]


class DfTransform(Enum):
    categorical_distribution = "categorical_distribution"
    numeric_distribution = "numeric_distribution"


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

