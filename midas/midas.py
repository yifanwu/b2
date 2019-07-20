from __future__ import absolute_import

from . import utils
import json
import uuid
import copy
from pandas import Dataframe
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


    def __register_df(self, df: Dataframe, meta_data: DfMetaData):
        """pivate method to keep track of dfs
        """
        self.dfs.append({
            df,
            meta_data
        })
        self.__show_or_rename_visualization()


    def __show_or_rename_visualization(self):
        raise NotImplementedError("__show_visualization needs to understand event between phospher")


    def get_current_widget(self):
        # TODO: show all the dfs (cut off at 5)
        return self.visualize_df_without_spec(self.dfs[-1])

        
    def touch(self, pd):
        """instrumentation of data acess
            this only works when 
            TODO:
            - need to figure out how to know when a df is just being displayed (there must be a display function?)
        """
        self.pd = pd

        old_read_csv = pd.read_csv
        def new_read_csv(path: str, **kwargs):
            """a wrapper layer on top of the pandas read_csv
            """
            df = old_read_csv(path, kwargs)
            meta_data = DfMetaData(time_created = datetime.now())
            self.__register_df(df, meta_data)
            return df
        setattr(pd, "read_csv", new_read_csv)

        # same as csv
        old_read_json = pd.read_json
        def new_read_json(path: str, **kwargs):
            """a wrapper layer on top of the pandas read_csv
            """
            df = old_read_json(path, kwargs)
            meta_data = DfMetaData(time_created = datetime.now())
            self.__register_df(df, meta_data)
            return df
        setattr(pd, "read_json", new_read_json)


    def add_dfs(self, *argv: Dataframe):
        meta_data = DfMetaData(time_created = datetime.now())
        for df in argv:
            self.__register_df(df, meta_data)


    def get_df_to_visualize_from_context(self):
        raise NotImplementedError()
    # note that spec is defaulted to none without the Optional signature because there is no typing for JSON.
    def visualize_df(self, df=Optional[Dataframe], spec=None):
        # generate default spec
        if (df == None):
            df = self.get_df_to_visualize_from_context()
        if (spec == None):
            return self.visualize_df_without_spec(df)
        else:
            return self.visualize_df_with_spec(df, spec)
    def visualize_df_without_spec(self, df: Dataframe):
        spec = gen_spec(df)
        return MidasWidget(spec)

    def visualize_df_with_spec(self, df: Dataframe, spec):
        return MidasWidget(spec, df)
    
__all__ = ['Midas']
# , 'entry_point_renderer']
