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


# four kinds of callbacks that the developer could add to
PredicateCallback = Callable[[SelectionPredicate], None]
DataFrameCallback =  Callable[[MidasDataFrame], None]
DataFrameToDataFrameCallback = Callable[[MidasDataFrame], MidasDataFrame]
PredicateToDataFrameCallback = Callable[[SelectionPredicate], MidasDataFrame]

    
class TickItem(NamedTuple):
    """[summary]
    
    Arguments:
        param_type {[BindingParamType]} -- [description]
        output_type {BindingOutputType}
        call
        target_df(optional)
    """
    param_type: TickIOType
    output_type: TickIOType
    call: Union[PredicateCallback, DataFrameCallback, DataFrameToDataFrameCallback, PredicateToDataFrameCallback]
    target_df: Optional[DFName]
    last_called: Optional[datetime] = None
