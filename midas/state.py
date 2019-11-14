from pandas import DataFrame  # type: ignore
from datetime import datetime
from typing import Dict, List

from .midas_algebra.dataframe import MidasDataFrame, DFInfo
from .util.errors import InternalLogicalError, debug_log
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

    # FIXME: maybe in the future df_name could be just added to DataFrame
    # @check_df_name
    def add_df(self, mdf: MidasDataFrame, is_base_df: bool=False):
        debug_log("adding df")
        if mdf.df_name is None:
            raise InternalLogicalError("df should have a name to be updated")
        created_on = datetime.now()
        selections: List[SelectionEvent] = []
        df_info = DFInfo(mdf, created_on, selections)
        # if 
        if (mdf.df_name in self.dfs):
            self.dfs[mdf.df_name] = self.dfs[mdf.df_name]._replace(df = mdf)
        else:
            self.dfs[mdf.df_name] = df_info # type: ignore 
            # we also need to manage the UI component
        if is_base_df:
            self.ui_comm.create_profile(mdf)
        else:
            self.ui_comm.visualize(mdf)
        return

    def has_df(self, df_name: DFName):
        return df_name in self.dfs


    def append_df_predicates(self, df_name: DFName, predicate: SelectionEvent) -> DFInfo:
        df_info = self.dfs.get(df_name)
        # idx = len(df_info.predicates)
        if df_info:
            df_info.predicates.append(predicate)
            return df_info
        raise InternalLogicalError(f"Df ({df_name}) should be defined!")


    def get_df(self, df_name: DFName):
        return self.dfs.get(df_name)


    def remove_df(self, df_name: DFName):
        self.dfs.pop(df_name)
