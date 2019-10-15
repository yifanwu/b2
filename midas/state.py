from pandas import DataFrame
from .midas_algebra.dataframe import MidasDataFrame
from datetime import datetime
from typing import Dict, List

from .util.errors import InternalLogicalError
from .vis_types import SelectionPredicate
from .state_types import DFInfo, DFName
from midas.ui_comm import UiComm

class State(object):
    dfs: Dict[DFName, DFInfo]
    # series: Dict[str, Ser]
    nextId: int

    def __init__(self, uiComm: UiComm):
        self.dfs = {}
        self.groupbys = {}
        self.ui_comm = uiComm


    # FIXME: maybe in the future df_name could be just added to DataFrame
    def add_df(self, df_name: DFName, mdf: MidasDataFrame):
        created_on = datetime.now()
        selections: List[SelectionPredicate] = []
        df_info = DFInfo(df_name, mdf, created_on, selections)
        self.dfs[df_name] = df_info
        # we also need to manage the UI component
        self.ui_comm.visualize(df_name, mdf)
        # maybe let's see what if we do not replace the index
        # if replace_index:
        #     df.index = df.index.map(str).map(lambda x: f"{x}-{df_name}")
        #     df.index.name = CUSTOM_INDEX_NAME
        return


    def update_df_data(self, df_name: DFName, mdf: MidasDataFrame):
        # will trigger the UI to update
        if self.has_df(df_name):
            self.dfs[df_name] = self.dfs[df_name]._replace(df = mdf)
        else:
            self.add_df(df_name, mdf)


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
