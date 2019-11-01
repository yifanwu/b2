from typing import Dict, List, Union, Optional, cast
from datetime import datetime, timedelta
from pandas import DataFrame

from midas.state_types import DFName
from midas.midas_algebra.dataframe import MidasDataFrame
from midas.vis_types import SelectionPredicate

from .event_types import TickSpec, TickItem

from .state import State
from .util.errors import logging, report_error_to_user, InternalLogicalError
from .util.helper import get_df_by_predicate, get_selection_by_predicate

class EventLoop(object):
    current_tick: int
    tick_funcs: Dict[DFName, List[TickItem]]
    tick_log: List[TickSpec]
    state: State

    def __init__(self, state: State):
        self.tick_funcs = {}
        self.current_tick = 0
        self.tick_log = []
        self.state = state


    def add_callback(self, item: TickItem):
        logging("add_to_tick", f" called{item.df_name}\n{item}")
        if (item.df_name in self.tick_funcs):
            self.tick_funcs[item.df_name].append(item)
        else:
            self.tick_funcs[item.df_name] = [item]


    def tick(self, df_name: DFName, predicate: SelectionPredicate):
        # tell state to change
        df_info = self.state.append_df_predicates(df_name, predicate)
        self.current_tick += 1
        self.tick_log.append(TickSpec(self.current_tick, df_name, datetime.now()))
        logging("tick", f"processing {df_name} with history {self.current_tick}")
        # TODO check if predicate the same as before
        # lineage_data: DataFrame = None
        items = self.tick_funcs.get(df_name)
        logging("tick", f"for predicate{predicate}")
        # def update_df(new_data: MidasDataFrame):
        #     if (new_data is not None) and (len(new_data.value.index) > 0):
        #         # register data if this is the first time that this is called
        #         
        #     else:
        #         report_error_to_user(f"Transformation result on {df_name} was empty")

        # def process_item(lineage_data: DataFrame,
        #     output_type: TickIOType,
        #     param_type: TickIOType,
        #     _call: Union[PredicateCallback, DataFrameCallback,
        #                  DataFrameToDataFrameCallback, PredicateToDataFrameCallback],
        #     target_df: Optional[DFName] = None):
        #     if (output_type == TickIOType.data) and (not target_df):
        #         raise InternalLogicalError("target_df should be defined")
        #     if (param_type == TickIOType.data) and (lineage_data is None):
        #         lineage_data = get_df_by_predicate(df_info.df, predicate)

        #     _target_df = target_df if target_df else DFName("ERROR") # hack to make pyright happy
        #     if (output_type == TickIOType.data) and (param_type == TickIOType.data):
        #         current_call = cast(DataFrameToDataFrameCallback, _call)
        #         new_data = current_call(lineage_data)
        #         update_df(new_data, _target_df)
        #     elif (output_type == TickIOType.data) and (param_type == TickIOType.predicate):
        #         # has to do this to make the type checker happy
        #         current_call = cast(PredicateToDataFrameCallback, _call)
        #         new_data = current_call(predicate)
        #         update_df(new_data, _target_df)
        #     elif (output_type == TickIOType.void) and (param_type == TickIOType.predicate):
        #         current_call = cast(PredicateCallback, _call)
        #         return current_call(predicate)
        #     elif (output_type == TickIOType.void) and (param_type == TickIOType.data):
        #         if lineage_data is None:
        #             lineage_data = get_df_by_predicate(df_info.df, predicate)
        #         return _call(lineage_data)
        #     else:
        #         raise InternalLogicalError(f"not all cases handled: {output_type}, {param_type}")

        # now run
        if items:
            for _, i in enumerate(items):
                r = i.call(predicate)

                # process_item(lineage_data, i.call, i.target_df)

