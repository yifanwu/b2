from typing import Dict, List
from datetime import datetime, timedelta

from .types import TickSpec, DfTransform, TickItem, \
    PredicateCallback, DataFrameCallback, PredicateToDataFrameCallback, DataFrameToDataFrameCallback, \
    TickIOType    

from .state import State
from .util.errors import logging
from .util.helper import get_df_by_predicate, get_selection_by_predicate


class EventLoop(object):
    current_tick: int
    tick_funcs: Dict[str, List[TickItem]]
    tick_log: List[TickSpec]
    state: State

    def __init__(self, state: State):
        self.tick_funcs = {}
        self.current_tick = 0
        self.tick_log = []
        self.state = state


    def _add_to_tick(self, df_name: str, item: TickItem):
        logging("_add_to_tick", f" called{df_name}\n{item}")
        if (df_name in self.tick_funcs):
            self.tick_funcs[df_name].append(item)
        else:
            self.tick_funcs[df_name] = [item]



    def _tick(self, df_name: str, history_index: int):
        self.tick_log.append(TickSpec(df_name, history_index, datetime.now()))
        logging("tick", f"processing {df_name} with history {history_index}")
        print("actually processing")
        self._process_tick(df_name, history_index)
        return

    def _process_tick(self, df_name: str, history_index: int):
        self.current_tick += 1
        df_info = self.dfs[df_name]
        if df_info is None:
            return
        _predicate = get_selection_by_predicate(df_info, history_index)

        if not _predicate:
            return
        # weird hack to make pyright happy...
        predicate = _predicate
        # TODO check if predicate the same as before
        lineage_data: DataFrame = None
        items = self.tick_funcs.get(df_name)
        logging("tick", f"for predicate{predicate}")
        def update_df(new_data: DataFrame, target_df: str):
            if (new_data is not None) and (len(new_data.index) > 0):
                # register data if this is the first time that this is called
                if not self._has_df(target_df):
                    self.register_df(new_data, target_df)
                else:
                    # see if we need to do any transforms..
                    vis_data = new_data
                    # we need to look up the target...
                    df_target_additional_transforms = self.dfs[target_df].visualization.chart_info.additional_transforms
                    if (df_target_additional_transforms == DfTransform.categorical_distribution):
                        first_col = new_data.columns.values[0]
                        vis_data = get_categorical_distribution(new_data[first_col], first_col)
                    elif (df_target_additional_transforms == DfTransform.numeric_distribution):
                        first_col = new_data.columns.values[0]
                        vis_data = get_numeric_distribution(new_data[first_col], first_col)

                    # update the data in store
                    self.set_df_data(target_df, new_data)
                    # send the update
                    vis = self.dfs[target_df].visualization
                    if vis:
                        vis.widget.replace_data(vis_data)
            else:
                report_error_to_user(f"Transformation result on {df_name} was empty")

        def process_item(lineage_data: DataFrame,
            output_type: TickIOType,
            param_type: TickIOType,
            _call: Union[PredicateCallback, DataFrameCallback,
                         DataFrameToDataFrameCallback, PredicateToDataFrameCallback],
            target_df: Optional[str] = None):
            if (output_type == TickIOType.data) and (not target_df):
                raise InternalLogicalError("target_df should be defined")
            if (param_type == TickIOType.data) and (lineage_data is None):
                    lineage_data = get_df_by_predicate(df_info.df, predicate)

            _target_df = target_df if target_df else "ERROR" # hack to make pyright happy
            if (output_type == TickIOType.data) and (param_type == TickIOType.data):
                new_data = _call(lineage_data)
                update_df(new_data, _target_df)
            elif (output_type == TickIOType.data) and (param_type == TickIOType.predicate):
                new_data = _call(lineage_data)
                update_df(new_data, _target_df)
            elif (output_type == TickIOType.void) and (param_type == TickIOType.predicate):
                return _call(predicate)
            elif (output_type == TickIOType.void) and (param_type == TickIOType.data):
                if lineage_data is None:
                    lineage_data = get_df_by_predicate(df_info.df, predicate)
                return _call(lineage_data)
            else:
                raise InternalLogicalError(f"not all cases handled: {output_type}, {param_type}")

        # now run
        if items:
            for _, i in enumerate(items):
                process_item(lineage_data, i.output_type, i.param_type, i.call, i.target_df)

