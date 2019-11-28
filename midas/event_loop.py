from midas.midas_algebra.dataframe import VisualizedDFInfo
from midas.midas_algebra.context import Context
from midas.vis_types import SelectionEvent
from typing import Dict, Callable, List, Any
from datetime import datetime

from midas.state_types import DFName
from .event_types import TickSpec, TickItem
from .config import MidasConfig
from .util.errors import logging, debug_log


def gather_current_selection(current_selection: Dict[DFName, SelectionEvent], df_name: DFName) -> List[SelectionEvent]:
    # FIXME: filter by relevant selections
    predicates: List[SelectionEvent] = []
    for a_df in current_selection:
        if a_df != df_name:
            predicates.append(current_selection[a_df])
    return predicates
    

class EventLoop(object):
    current_tick: int
    tick_funcs: Dict[DFName, List[TickItem]]
    tick_log: List[TickSpec]
    send_debug_msg: Callable[[str], Any]

    def __init__(self, context: Context, dfs_ref, config: MidasConfig):
        self.tick_funcs = {}
        self.current_tick = 0
        self.tick_log = []
        self.context = context
        self.dfs_ref = dfs_ref
        self.config = config
        

    def add_callback(self, item: TickItem):
        logging("add_to_tick", f" called{item.df_name}\n{item}")
        if (item.df_name in self.tick_funcs):
            self.tick_funcs[item.df_name].append(item)
        else:
            self.tick_funcs[item.df_name] = [item]


    def tick(self, df_name: DFName, current_predicate: SelectionEvent, all_predicate: Dict[DFName, SelectionEvent]):
        # tell state to change
        self.current_tick += 1
        self.tick_log.append(TickSpec(self.current_tick, df_name, datetime.now()))
        logging("tick", f"processing {df_name} for predicate{all_predicate}")
        # TODO check if predicate the same as before
        items = self.tick_funcs.get(df_name)

        # update the charts if there are linking by default
        #   we would need to access all that is currently selected and update the charts
        if self.config.linked:
            # ELSE we would know that the invididual links would be greated
            # note that we need to put it into a list, because otherwise it's an interator 
            #   and we are modifying state, for instance, when we do a join, a a new df_name might be inserted
            for a_df_name in list(self.dfs_ref):
                df_info = self.dfs_ref[a_df_name]
                if isinstance(df_info, VisualizedDFInfo):
                    s = gather_current_selection(all_predicate, a_df_name)
                    if len(s) > 0:
                        # debug_log("applying the filtering logic")
                        new_df = df_info.original_df.apply_selection(s)
                        new_df.df_name = a_df_name
                        new_df.show()

        if items:
            for _, i in enumerate(items):
                r = i.call(current_predicate)    