from enum import Enum
from midas.midas_algebra.selection import SelectionValue
from midas.state_types import DFName
from typing import NamedTuple, Callable, List, Any
from datetime import datetime

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
    call: Callable[[List[SelectionValue]], Any]
    # visualize: bool