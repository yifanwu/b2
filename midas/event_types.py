from enum import Enum
from midas.state_types import DFName
from typing import NamedTuple, Callable, List, Union, Any, Optional, Dict, Tuple
from datetime import datetime
from midas.midas_algebra.dataframe import MidasDataFrame

from .vis_types import SelectionPredicate


class TickIOType(Enum):
    predicate = "predicate"
    data = "data"
    void = "void"


class TickSpec(NamedTuple):
    step: int
    df_name: str
    start_time: datetime


class TickItem(NamedTuple):
    df_name: DFName
    call: Callable[[SelectionPredicate], Any]
    # visualize: bool