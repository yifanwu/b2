from midas.midas_algebra.selection import SelectionValue
from midas.midas_algebra.dataframe import VisualizedDFInfo
from midas.midas_algebra.context import Context
from midas.vis_types import SelectionEvent
from typing import Dict, Callable, List, Any, cast, Optional
from datetime import datetime

from midas.state_types import DFName
from .event_types import TickSpec, TickItem
from .config import MidasConfig
from .util.errors import logging, debug_log


# def gather_current_selection(current_selection: Dict[DFName, SelectionEvent], df_name: DFName) -> List[SelectionEvent]:
#     # FIXME: filter by relevant selections
#     predicates: List[SelectionEvent] = []
#     for a_df in current_selection:
#         if a_df != df_name:
#             predicates.append(current_selection[a_df])
#     # debug_log(f"Current selections: {predicates}")
#     return predicates
    

class EventLoop(object):
    current_tick: int
    tick_funcs: Dict[DFName, List[TickItem]]
    # tick_log: List[TickSpec]
    send_debug_msg: Callable[[str], Any]

    def __init__(self, context: Context, dfs_ref, config: MidasConfig):
        self.tick_funcs = {}
        self.current_tick = 0
        # self.tick_log = []
        self.context = context
        self.dfs_ref = dfs_ref
        self.config = config
        

    def add_callback(self, item: TickItem):
        logging("add_to_tick", f" called{item.df_name}\n{item}")
        if (item.df_name in self.tick_funcs):
            self.tick_funcs[item.df_name].append(item)
        else:
            self.tick_funcs[item.df_name] = [item]

        # items = self.tick_funcs.get(df_name)
        # if items:
        #     for _, i in enumerate(items):
        #         r = i.call(current_predicate)    