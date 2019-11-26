from datetime import datetime
from typing import Dict, List

from .midas_algebra.dataframe import MidasDataFrame, DFInfo, VisualizedDFInfo
from .util.errors import InternalLogicalError, debug_log, type_check_with_warning
from .vis_types import SelectionEvent
from .state_types import DFName
from .ui_comm import UiComm


class State(object):
    # FIXME: we might want to support a history of MidasDataFrames! as opposed to an update in place for dfinfo
    dfs: Dict[DFName, DFInfo]
    # series: Dict[str, Ser]
    nextId: int

    def __init__(self, uiComm: UiComm):
        self.dfs = {}
        self.groupbys = {}
        self.ui_comm = uiComm
        self.shelf_selections = {}

    def add_df(self, mdf: MidasDataFrame, config):
        # debug_log("adding df")
        # type_check_with_warning(mdf, MidasDataFrame)
        if mdf.df_name is None:
            raise InternalLogicalError("df should have a name to be updated")

        is_visualized = False
        if config.is_base_df:
            self.ui_comm.create_profile(mdf)
            # if base_df only has two columns, try to visualize!
        # else:
        is_visualized = self.ui_comm.visualize(mdf)
        
        if (mdf.df_name in self.dfs):
            debug_log(f"changing df {mdf.df_name} value")
            self.dfs[mdf.df_name].update_df(mdf)
        else:
            if is_visualized:
                df_info = VisualizedDFInfo(mdf)
            else:
                df_info = DFInfo(mdf)
            self.dfs[mdf.df_name] = df_info
        return


    def has_df(self, df_name: DFName):
        return df_name in self.dfs


    def append_df_predicates(self, selection: SelectionEvent) -> DFInfo:
        df_name = selection.df_name
        df_info = self.dfs.get(df_name)
        # idx = len(df_info.predicates)
        if df_info and isinstance(df_info, VisualizedDFInfo):
            df_info.predicates.append(selection)
            return df_info
        else:
            raise InternalLogicalError(f"Df ({df_name}) should be defined and be visualized as a chart!")


    def get_df(self, df_name: DFName):
        return self.dfs.get(df_name)


    def remove_df(self, df_name: DFName):
        self.dfs.pop(df_name)
