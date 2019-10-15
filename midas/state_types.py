from enum import Enum
from typing import NamedTuple, Callable, List, NewType, Union, Any, Optional, Dict, Tuple
from datetime import datetime
from midas.midas_algebra.dataframe import MidasDataFrame

from .vis_types import SelectionPredicate

DFName = NewType('DFName', str)

class DFInfo(NamedTuple):
    name: DFName
    df: MidasDataFrame
    created_on: datetime
    predicates: List[SelectionPredicate]