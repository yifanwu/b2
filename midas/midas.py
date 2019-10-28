from __future__ import absolute_import
from pandas import DataFrame, Series
from IPython import get_ipython
from typing import Dict, Optional, List, Callable, Union, cast
# from datetime import datetime
# from pyperclip import copy

try:
    from IPython.display import display
except ImportError as err:
    print("not in Notebook environment")
    display = lambda x: None
    logging = lambda x, y: None


from .midas_algebra.dataframe import MidasDataFrame
from midas.state_types import DFName, DFInfo
from .state import State
from .ui_comm import UiComm
# from .config import DEBOUNCE_RATE_MS
from .midas_magic import MidasMagic
from .util.instructions import HELP_INSTRUCTION
from .util.errors import NullValueError, DfNotFoundError, InternalLogicalError, UserError, logging, check_not_null
from .util.utils import isnotebook
from .util.helper import get_df_by_predicate

from .event_loop import EventLoop
from .event_types import TickItem, TickIOType

is_in_ipynb = isnotebook()

class Midas(object):
    """[summary]
    The Midas object holds the environment that controls different dataframes
    """
    magic: MidasMagic
    ui_comm: UiComm
    state: State
    shelf_selections: dict #TODO Change

    def __init__(self):
        # self.is_processing_tick: bool = False
        self.midas_cell_comm = None
        # FIXME: have a better mock up experience for testing, if we are not in notebook...
        # check if we are in a ipython environment
        ui_comm = UiComm(is_in_ipynb)
        self.ui_comm = ui_comm
        self.shelf_selections = {}
        self.state = State(ui_comm)
        self.event_loop = EventLoop(self.state)
        if is_in_ipynb:
            ip = get_ipython()
            magics = MidasMagic(ip, ui_comm)
            ip.register_magics(magics)


    def register_df(self, df_name_raw: str, df_raw: DataFrame):
        """we will add this both to state
           and to render
        """
        df_name = DFName(df_name_raw)
        logging("register_df", df_name)
        # create MidasDataFrame
        df = MidasDataFrame.from_data(df_raw)
        self.state.add_df(df_name, df)
        return


    def has_df(self, df_name_raw: str):
        return self.state.has_df(DFName(df_name_raw))

    def register_series(self, series: Series, name: str):
        # turn it into a df
        df = series.to_frame()
        return self.register_df(df, name)


    def get_current_selection(self, df_name: DFName, option: str="predicate"):
        """[summary]
        
        Arguments:
            df_name {str} -- [description]
            option {str} -- two options, "predicate" or "data", defaults to "predicate"
        
        Returns:
            [type] -- [description]
        """
        df_info = self.get_df_info(df_name)
        check_not_null(df_info)
        if (len(df_info.predicates) > 0):
            predicate = df_info.predicates[-1]
            if (option == "predicate"):
                return predicate
            else:
                return get_df_by_predicate(df_info.df, predicate)
        else:
            return None


    # the re
    def get_df_info(self, df_name: DFName) -> Optional[DFInfo]:
        return self.state.dfs.get(df_name)


    def get_df_vis_info(self, df_name: str):
        return self.ui_comm.vis_spec.get(DFName(df_name))


    @staticmethod
    def help():
        print(HELP_INSTRUCTION)

    def add_selection(self, df_name: DFName, selection: str):
        # note that the selection is str because 
        logging("js_add_selection", df_name)
        # figure out what spec it was
        # FIXME make sure this null checking is correct
        predicate = self.ui_comm.get_predicate_info(df_name, selection)
        self.event_loop.tick(df_name, predicate)
        return


    # decorator
    # def bind(self, param_type: Union[TickIOType, str], output_type: Union[TickIOType, str], df_interact_name: str, target_df: Optional[str]=None):
    #     if not (self.state.has_df(df_interact_name)):
    #         raise DfNotFoundError(f"{df_interact_name} is not in the collection of {self.dfs.keys()}")
    #     if target_df and (target_df in self.dfs):
    #         raise UserError(f"Your result based df {df_interact_name} alread exists, please chose a new name")
        
    #     _param_type = cast(TickIOType, TickIOType[param_type] if (type(param_type) == str) else param_type)
    #     _output_type = cast(TickIOType, TickIOType[output_type] if (type(param_type) == str) else output_type)
    #     def decorator(call):
    #         nonlocal target_df
    #         if (_output_type == TickIOType.data) and (not target_df):
    #             rand_hash = get_random_string(4)
    #             target_df = f"{call.__name__}_on_{df_interact_name}_{rand_hash}"
    #         item = TickItem(_param_type, _output_type, call, target_df)
    #         self.event_loop.add_to_tick(df_interact_name, item)
    #     return decorator


    # def register_join_info(self, dfs: List[str], join_columns: List[str]):
    #     join_info = JoinInfo(dfs, join_columns)
    #     self.joins.append(join_info)


    def add_facet(self, df_name: str, facet_column: str):
        # 
        raise NotImplementedError()
    

    def js_update_selection_shelf_selection_name(self, old_name: str, new_name: str):
      self.state.shelf_selections[new_name] = self.state.shelf_selections[old_name]
      del self.state.shelf_selections[old_name]
    

    def js_remove_selection_from_shelf(self, df_name: str):
      del self.shelf_selections[df_name]


    def js_add_selection_to_shelf(self, df_name: str):
        if self.state.has_df(df_name):
            predicates = self.state.dfs[df_name].predicates
            if (len(predicates) > 0):
                predicate = predicates[-1]

                name = f"{predicate.x_column}_{predicate.x[0]}_{predicate.x[-1]}"
                if name in self.state.shelf_selections:
                  new_name = name
                  counter = 1
                  while new_name in self.state.shelf_selections:
                    new_name = name
                    name += str(counter)
                  name = new_name

                self.state.shelf_selections[name] = (predicate, df_name)
                self.midas_cell_comm.send({
                  'type': 'add-selection',
                  'value': name
                })
        else: 
            self.midas_cell_comm.send({
            'type': 'error',
            'value': f'no selection on {df_name} yet'
        })


    # def js_get_current_chart_code(self, df_name: str) -> Optional[str]:
    #     # figure out how to derive the current df
    #     # don't have a story yet for complicated things...
    #     # decide on if we want to focus on complex code gen...
    #     if self._has_df(df_name):
    #         predicates = self.dfs[df_name].predicates
    #         if (len(predicates) > 0):
    #             predicate = predicates[-1]
    #             code = get_df_code(predicate, df_name)
    #             print(code)
    #             copy(code)
    #             return code
    #     # something went wrong, so let's tell comes...
    #     self.midas_cell_comm.send({
    #         'type': 'error',
    #         'value': f'no selection on {df_name} yet'
    #     })
    #     return

    # # the following are for internal use
    # def js_add_selection(self, df_name: str, selection: str):
    #     logging("js_add_selection", df_name)
    #     # figure out what spec it was
    #     # FIXME make sure this null checking is correct
    #     predicate = self.ui_comm.get_predicate_info(df_name, selection)
    #     self.event_loop.tick(df_name, predicate)
    #     return


# def load_ipython_extension(ipython):
# # ip = get_ipython()
#     magics = Midas(ipython)
#     ipython.register_magics(magics)


__all__ = ['Midas']
