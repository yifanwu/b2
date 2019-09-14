from pandas import DataFrame
from typing import Dict
from .types import DFInfo

class State(object):
    dfs: Dict[str, DFInfo]
    groupbys: Dict[str, ]
    series: Dict[str, ]
    nextId: int

    def __init__(self):
        self.dfs = {}

    def add_df(self, df_name: str, df: DataFrame):
        self.dfs[df_name] = df

    def get_df(self, df_name: str):
        return self.dfs.get(df_name)

    def remove_df(self, df_name: str):
        self.dfs.pop(df_name)



    def _next_id(self):
      to_return = self.nextId
      self.nextId += 1
      return to_return

    def _has_df(self, df_name: str):
        if (df_name in self.dfs):
            return True
        else:
            return False

    def _get_id(self, df_name: str):
        if self._has_df(df_name):
          return self.dfs[df_name].df_id
        else:
          return self._next_id()
