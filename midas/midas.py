from __future__ import absolute_import

from . import utils
import json
import uuid
import copy
from pandas import DataFrame, read_csv, read_json
from types import MethodType
from typing import Optional
from datetime import datetime

from IPython.display import display, publish_display_data

from .utils import prepare_spec
from .showme import gen_spec
from .widget import MidasWidget
from .types import DfMetaData

import types

class Midas(object):
    
    def __init__(self):
        self.dfs = []


    def __register_df(self, df: DataFrame, meta_data: DfMetaData):
        """pivate method to keep track of dfs
        TODO: make the meta_data work with the objects
        """
        self.dfs.append(df)
        self.__show_or_rename_visualization()


    def __show_or_rename_visualization(self):
        # raise NotImplementedError("__show_visualization needs to understand event between phospher")
        print("showing visualization")


    def get_current_widget(self):
        # TODO: show all the dfs (cut off at 5)
        return self.visualize_df_without_spec(self.dfs[-1])

    def read_json(self, path: str, **kwargs):
        df = read_json(path, kwargs)
        meta_data = DfMetaData(time_created = datetime.now())
        self.__register_df(df, meta_data)
        return df


    def read_csv(self, path: str, **kwargs):
        df = read_csv(path, kwargs)
        meta_data = DfMetaData(time_created = datetime.now())
        self.__register_df(df, meta_data)
        return df


    def add_dfs(self, *argv: DataFrame):
        meta_data = DfMetaData(time_created = datetime.now())
        for df in argv:
            self.__register_df(df, meta_data)


    def get_df_to_visualize_from_context(self):
        raise NotImplementedError()
    # note that spec is defaulted to none without the Optional signature because there is no typing for JSON.
    def visualize_df(self, df=Optional[DataFrame], spec=None):
        # generate default spec
        if (df == None):
            df = self.get_df_to_visualize_from_context()
        if (spec == None):
            return self.visualize_df_without_spec(df)
        else:
            return self.visualize_df_with_spec(df, spec)
    def visualize_df_without_spec(self, df: DataFrame):
        spec = gen_spec(df)
        return MidasWidget(spec)

    def visualize_df_with_spec(self, df: DataFrame, spec):
        return MidasWidget(spec, df)
    
__all__ = ['Midas']
# , 'entry_point_renderer']
