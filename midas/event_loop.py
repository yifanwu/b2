from typing import Dict, Callable, List, Any
from datetime import datetime

from midas.state_types import DFName
from midas.vis_types import SelectionPredicate

from .event_types import TickSpec, TickItem

from .state import State
from .util.errors import logging

class EventLoop(object):
    current_tick: int
    tick_funcs: Dict[DFName, List[TickItem]]
    tick_log: List[TickSpec]
    state: State
    send_debug_msg: Callable[[str], Any]

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

        # now run
        if items:
            for _, i in enumerate(items):
                r = i.call(predicate)

                # process_item(lineage_data, i.call, i.target_df)

