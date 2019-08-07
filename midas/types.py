from enum import Enum
from typing import NamedTuple, Callable, List, Union, Any, Optional, Dict, Tuple
from datetime import datetime
from pandas import DataFrame

from .widget import MidasWidget

"""
Note that namedtuples are immutable, so we'll basically 
"""

# hack
VegaSpecType = Dict[str, Any]

class ChartType(Enum):
    bar_categorical = "bar_categorical"
    bar_linear = "bar_linear"
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


class TickCallbackType(Enum):
    dataframe = "dataframe"
    predicate = "predicate"


class JoinInfo(NamedTuple):
    dfs: List[str]
    join_colums: List[str]


class TickSpec(NamedTuple):
    df_name: str
    history_index: int
    start_time: datetime


class DFLoc(NamedTuple):
    rows: Union[slice, List[int]]
    columns: Union[slice, List[str]]

    
# TODO: we need a new derivation that captures functions applied
# class DF, Callable[]

class DFDerivation(NamedTuple):
    soruce_df: str
    target_df: str
    # some domain specific annotations
    derivation_type: DerivationType
    derivation_func: Union[Callable[[DataFrame], DataFrame], DFLoc]
    # dataframe in, dataframe out


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


class OneDimSelectionPredicate(NamedTuple):
    interaction_time: datetime
    x_column: str
    is_categoritcal: bool
    # the first is selecting linear scale, the second categorical scale
    x: Union[Tuple[float, float], List[str]]
    dimension = 1
    

SelectionPredicate = Union[TwoDimSelectionPredicate, OneDimSelectionPredicate]

PredicateCallback = Callable[[SelectionPredicate], None]


class DataFrameCall(NamedTuple):
    func: Callable[[DataFrame], DataFrame]
    target_df: str

class PredicateCall(NamedTuple):
    func: PredicateCallback
    

class TickItem(NamedTuple):
    callback_type: TickCallbackType
    call: Union[DataFrameCall, PredicateCall]
    throttle_rate: Optional[float] = None
    last_called: Optional[datetime] = None


class ChartInfo(NamedTuple):
    chart_type: ChartType
    # ASK Arvind: this seems to be redundant information to the vega spec?
    encodings: Dict[Channel, str]
    vega_spec: VegaSpecType


class Visualization(NamedTuple):
    chart_info: ChartInfo
    widget: MidasWidget


class DFInfo(NamedTuple):
    df_name: str
    df: DataFrame
    created_on: datetime
    predicates: List[SelectionPredicate]
    derivation: DFDerivation
    visualization: Optional[Visualization] = None
    