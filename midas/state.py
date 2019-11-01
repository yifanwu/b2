from pandas import DataFrame
from .midas_algebra.dataframe import MidasDataFrame, DFInfo
from datetime import datetime
from typing import Dict, List

from .util.errors import InternalLogicalError
from .vis_types import SelectionPredicate
from .state_types import DFName
from midas.ui_comm import UiComm


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
    def add_df(self, mdf: MidasDataFrame):
        if mdf.df_name is None:
            raise InternalLogicalError("df should have a name to be updated")
        created_on = datetime.now()
        selections: List[SelectionPredicate] = []
        df_info = DFInfo(mdf, created_on, selections)
        self.dfs[mdf.df_name] = df_info # type: ignore 
        # we also need to manage the UI component
        self.ui_comm.visualize(mdf)
        # maybe let's see what if we do not replace the index
        # if replace_index:
        #     df.index = df.index.map(str).map(lambda x: f"{x}-{df_name}")
        #     df.index.name = CUSTOM_INDEX_NAME
        return

    # @check_df_name
    def update_df(self, mdf: MidasDataFrame):
        if mdf.df_name is None:
            raise InternalLogicalError("df should have a name to be updated")
        # will trigger the UI to update
        if self.has_df(mdf.df_name):
            self.dfs[mdf.df_name] = self.dfs[mdf.df_name]._replace(df = mdf)
        else:
            self.add_df(mdf)


    def append_df_predicates(self, df_name: DFName, predicate: SelectionPredicate) -> DFInfo:
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


    def has_df(self, df_name: DFName):
        if (df_name in self.dfs):
            return True
        else:
            return False
