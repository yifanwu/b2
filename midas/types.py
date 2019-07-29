from enum import Enum
from typing import NamedTuple, Callable, List, Union, Any, Optional, Dict, Tuple
from datetime import datetime
from pandas import DataFrame

from .widget import MidasWidget

class ChartType(Enum):
    bar = "bar"
    scatter = "scatter"
    line = "line"


class Channel(Enum):
    x = "x"
    y = "y"
    color = "color"


class DerivationType(Enum):
    initial = "initial"
    loc = "loc" # projection and selection
    groupby = "groupby"
    black_box = "black_box"


class JoinInfo(NamedTuple):
    dfs: List[str]
    join_colums: List[str]


class DFLoc(NamedTuple):
    rows: slice
    columns: slice


class DFDerivation(NamedTuple):
    soruce_df: str
    target_df: str
    # some domain specific annotations
    derivation_type: DerivationType
    derivation_func: Union[Callable[[DataFrame], DataFrame], DFLoc]
    # dataframe in, dataframe out


class NullValueError(Exception):
    def __init__(self, message):
        super().__init__(message)


class TwoDimSelectionPredicate(NamedTuple):
    interaction_time: datetime
    x_column: str
    y_column: str
    x: Tuple[float, float]
    y: Tuple[float, float]


class OneDimSelectionPredicate(NamedTuple):
    interaction_time: datetime
    x_column: str
    x: Tuple[float, float]


PredicateCallback = Callable[[Union[TwoDimSelectionPredicate, OneDimSelectionPredicate]], None]


class TickItemBase:
    throttle_rate: Optional[float] = None
    last_called: Optional[datetime] = None

class TickItemNewDF(NamedTuple) :
    func: Callable[[DataFrame], DataFrame]
    target_df: str

class TickItemBlackBox(NamedTuple):
    predicate_func: PredicateCallback
    

TickItem = Union[TickItemNewDF, ]

class ChartSpec:
    chart_type: ChartType
    # ASK Arvind: this seems to be redundant information to the vega spec?
    encodings: Dict[Channel, str]
    vega_spec: Any

class Visualization(NamedTuple):
    chart_spec: ChartSpec
    widget: MidasWidget


class DFInfo(NamedTuple):
    df_name: str
    df: DataFrame
    created_on: datetime
    predicates: List[Union[TwoDimSelectionPredicate, OneDimSelectionPredicate]]
    derivation: DFDerivation
    visualization: Optional[Visualization] = None
    