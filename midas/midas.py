from __future__ import absolute_import

from . import utils
import json
import uuid
import copy
from pandas import DataFrame, read_csv, read_json
from types import MethodType
from typing import Optional, Dict, Any
from datetime import datetime

from IPython.display import display, publish_display_data

from .utils import prepare_spec
from .showme import gen_spec, set_data_attr, SELECTION_SIGNAL
from .widget import MidasWidget
# from .types import DfMetaData

import types

CUSTOM_FUNC_PREFIX = "__m_"
MIDAS_INSTANCE_NAME = "m"

class Midas(object):
    dfs: Dict[str, Any]

    def __init__(self, m_name=MIDAS_INSTANCE_NAME):
        self.dfs = {}
        self.m_name: str = m_name
        print("Initiated Midas")


    def df(self, df_name: str):
        # all the dfs are named via the global var so we can manipulate without worrying about reference changes!
        found = self.dfs[df_name]
        if (found != None):
            return found["df"]
        else:
            return None


    def register_df(self, df: DataFrame, df_name: str):
        """pivate method to keep track of dfs
        TODO: make the meta_data work with the objects
        """
        df_info = {}
        df_info["df"] = df
        df_info["created_on"] = datetime.now()
        df_info["df_name"] = df_name

        self.dfs[df_name] = df_info
        self.__show_or_rename_visualization()


    def __remove_df(self, df_name: str):
        self.dfs[df_name] = None


    def __show_or_rename_visualization(self):
        # raise NotImplementedError("__show_visualization needs to understand event between phospher")
        print("showing visualization")


    def get_current_widget(self):
        # TODO: show all the dfs (cut off at 5)
        current_obj = max(self.dfs.values(), key=lambda v: v["created_on"])
        if ((current_obj != None) & (current_obj["df_name"] != None)):
            df_name = current_obj["df_name"]
            print(df_name)
            return self.visualize_df_without_spec(df_name)
        else:
           return


    def read_json(self, path: str, df_name: str, **kwargs):
        df = read_json(path, kwargs)
        self.register_df(df, df_name)
        return df


    def read_csv(self, path: str, df_name: str, **kwargs):
        df = read_csv(path, kwargs)
        # meta_data = DfMetaData(time_created = datetime.now())
        self.register_df(df, df_name)
        return df


    def get_df_to_visualize_from_context(self):
        raise NotImplementedError()


    # note that spec is defaulted to none without the Optional signature because there is no typing for JSON.
    def visualize_df(self, df_name: str=None, spec=None):
        # generate default spec
        if (df_name == None):
            df = self.get_df_to_visualize_from_context()
        elif (spec == None):
            return self.visualize_df_without_spec(df_name)
        else:
            return self.visualize_df_with_spec(df_name, spec, True)


    def visualize_df_without_spec(self, df_name: str):
        df = self.df(df_name)
        spec = gen_spec(df)
        # set_data is false because gen_spec already sets the data
        return self.visualize_df_with_spec(df_name, spec, False)


    def visualize_df_with_spec(self, df_name: str, spec, set_data=False):
        if (set_data):
            df = self.df(df_name)
            spec = set_data_attr(spec, df)
        w = MidasWidget(spec)
        cb = f"""
            var {CUSTOM_FUNC_PREFIX}val_str = JSON.stringify(value);
            var pythonCommand = `
                from json import loads
                from pandas import DataFrame
                {CUSTOM_FUNC_PREFIX}loaded_data = loads('${{{CUSTOM_FUNC_PREFIX}val_str}}')
                {CUSTOM_FUNC_PREFIX}select_df = DataFrame({CUSTOM_FUNC_PREFIX}loaded_data, index=[0])
                {self.m_name}.df("{df_name}").selection={CUSTOM_FUNC_PREFIX}select_df
            `;
            console.log('pythonCommand', pythonCommand);
            IPython.notebook.kernel.execute(pythonCommand);
        """
        w.registerSignalCallback(SELECTION_SIGNAL, cb)
        return w


__all__ = ['Midas']
# , 'entry_point_renderer']
