from datetime import datetime
from enum import Enum
from midas.midas_algebra.selection import SelectionValue
from midas.state_types import DFName
from typing import NamedTuple, List, Any, Optional, Dict


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

class SelectionEvent():
    interaction_time: datetime
    predicate: List[SelectionValue]
    df_name: DFName


# class TwoDimSelectionPredicate(SelectionPredicate):
#     # assume that two dimension is both linear
#     def __init__(self, df_name: DFName, x_column: str, y_column: str, x: Tuple[float, float], y: Tuple[float, float]):
#         self.df_name = df_name
#         self.dimension = 2
#         self.interaction_time = datetime.now()
#         self.x_column = x_column
#         self.y_column = y_column
#         self.x = x
#         self.y = y


# class NullSelectionPredicate(SelectionPredicate):
#     def __init__(self, df_name: DFName):
#         self.df_name = df_name
#         self.dimension = 0
#         self.interaction_time = datetime.now()


# class OneDimSelectionPredicate(SelectionPredicate):
#     def __init__(self, df_name: DFName, x_column: str,
#       x: Union[Tuple[float, float], List[str]],
#       is_categoritcal: bool):
#         self.df_name = df_name
#         self.dimension = 1
#         self.interaction_time = datetime.now()
#         self.x_column = x_column
#         self.is_categoritcal = is_categoritcal
#         self.x = x


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

