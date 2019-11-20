from __future__ import absolute_import
from datetime import datetime
from IPython import get_ipython  # type: ignore
from typing import Optional, Union, List, Dict
from datascience import Table
# from pyperclip import copy

try:
    from IPython.display import display  # type: ignore
except ImportError as err:
    print("not in Notebook environment")
    display = lambda x: None
    logging = lambda x, y: None

from .stream import MidasSelectionStream

from midas.midas_algebra.dataframe import MidasDataFrame, DFInfo, RuntimeFunctions
from midas.midas_algebra.context import Context

from midas.vis_types import SelectionEvent
from midas.state_types import DFName
from midas.event_types import TickItem
from .state import State
from .ui_comm import UiComm
from .midas_magic import MidasMagic
from .util.instructions import HELP_INSTRUCTION
from .util.errors import UserError, logging, check_not_null
from .util.utils import isnotebook, find_name
from .config import default_midas_config, MIDAS_INSTANCE_NAME, MidasConfig
from .event_loop import EventLoop


is_in_ipynb = isnotebook()


class Midas(object):
    """[summary]
    The Midas object holds the environment that controls different dataframes
    """
    magic: MidasMagic
    ui_comm: UiComm
    state: State
    context: Context
    rt_funcs: RuntimeFunctions
    current_selection: Dict[DFName, SelectionEvent]

    def __init__(self, config: MidasConfig=default_midas_config):
        # check the assigned name, if it is not 'm', then complain
        assigned_name = find_name(True)
        if assigned_name is None:
            raise UserError("must assign a name")
        ui_comm = UiComm(is_in_ipynb, self.js_add_selection, assigned_name)
        self.ui_comm = ui_comm
        self.shelf_selections = {}
        self.state = State(ui_comm)
        self.context = Context(self.state.dfs)
        self.event_loop = EventLoop(self.context, self.state, config)
        self.current_selection = {}
        if is_in_ipynb:
            ip = get_ipython()
            magics = MidasMagic(ip, ui_comm)
            ip.register_magics(magics)

        self.rt_funcs = RuntimeFunctions(
            self.state.add_df,
            self.get_stream,
            self.ui_comm.navigate_to_chart,
            # self._eval,
            self.context.apply_selection)


    def from_records(self, records):
        table = Table.from_records(records)
        df_name = find_name()
        return MidasDataFrame.create_with_table(table, df_name, self.rt_funcs)


    def read_table(self, filepath_or_buffer, *args, **vargs):
        table = Table.read_table(filepath_or_buffer, *args, **vargs)
        df_name = find_name()
        return MidasDataFrame.create_with_table(table, df_name, self.rt_funcs)


    def with_columns(self, *labels_and_values, **formatter):
        table = Table().with_columns(*labels_and_values, **formatter)
        df_name = find_name()
        return MidasDataFrame.create_with_table(table, df_name, self.rt_funcs)


    def get_stream(self, df: Union[str, MidasDataFrame]) -> MidasSelectionStream:
        """[summary]
        
        Arguments:
            df -- could either be the name or the dataframe
        """
        # note that in the future we should
        #   consider putting this along with the dataframes
        # create the functions
        # then pass them to MidasSelectionStream
        if (isinstance(df, str)):
            df_name = DFName(df)
        else:
            df_name = df.df_name
            if (df_name is None):
                # FIXME: might place this function somewher else so they get the mental model easier?
                raise UserError("DF must be named to access selection")
        df_info = self.get_df_info(df_name)
        check_not_null(df_info)
        return MidasSelectionStream(df_name, df_info.predicates, self.bind)


    # @Shloak add join info here
    def add_join_info(self, join_info):
        self.context.add_info()
        


    def refresh_comm(self):
        self.ui_comm.set_comm()


    def has_df(self, df_name_raw: str):
        return self.state.has_df(DFName(df_name_raw))


    # the re
    def get_df_info(self, df_name: DFName) -> Optional[DFInfo]:
        return self.state.dfs.get(df_name)


    def get_df_vis_info(self, df_name: str):
        return self.ui_comm.vis_spec.get(DFName(df_name))


    @staticmethod
    def help():
        print(HELP_INSTRUCTION)


    def js_add_selection(self, selection: SelectionEvent):
        # cell_to_create = f"# based on your interaction on df {selection.df_name}"
        # self.create_cell_with_text(cell_to_create)
        # self.ui_comm.execute_current_cell()
        return


    def update_current_selection(self, selection: SelectionEvent):
        self.current_selection[selection.df_name] = selection
        # if selection.df_name in self.current_selection:
        return

    def add_selection_by_interaction(self, df_name_raw: str, value):
        df_name = DFName(df_name_raw)
        predicate = self.ui_comm.get_predicate_info(df_name, value)
        date = datetime.now()
        selection_event = SelectionEvent(date, predicate, DFName(df_name))
        self.add_selection(selection_event)


    def add_selection(self, selection: SelectionEvent):
        # note that the selection is str because 
        # logging("add_selection", df_name)
        self.state.append_df_predicates(selection)
        self.update_current_selection(selection)
        self.event_loop.tick(selection.df_name, selection, self.current_selection)
        return


    def create_cell_with_text(self, s):
        d = datetime.now()
        annotated = f"# auto-created on {d}\n{s}"
        get_ipython().set_next_input(annotated)
        # then execute it
        self.ui_comm.execute_current_cell()


    def bind(self, df_name: DFName, cb):
        item = TickItem(df_name, cb)
        return self.event_loop.add_callback(item)


    def add_facet(self, df_name: str, facet_column: str):
        # 
        raise NotImplementedError()
    

    def js_update_selection_shelf_selection_name(self, old_name: str, new_name: str):
      self.state.shelf_selections[new_name] = self.state.shelf_selections[old_name]
      del self.state.shelf_selections[old_name]
    

    def js_remove_selection_from_shelf(self, df_name: str):
      del self.shelf_selections[df_name]


    def js_add_selection_to_shelf(self, df_name_raw: str):
        df_name = DFName(df_name_raw)
        if self.state.has_df(df_name):
            predicates = self.state.dfs[df_name].predicates
            if (len(predicates) > 0):
                predicate = predicates[-1]
                # @RYAN: need to deal with the fact that the predicates are of 
                #        multiple possible types, below makes the assumption that it's 
                #        twoDimSelection
                name = f"{predicate.x_column}_{predicate.x[0]}_{predicate.x[-1]}" # type: ignore
                if name in self.state.shelf_selections:
                  new_name = name
                  counter = 1
                  while new_name in self.state.shelf_selections:
                    new_name = name
                    name += str(counter)
                  name = new_name

                self.state.shelf_selections[name] = (predicate, df_name)
                self.ui_comm.custom_message('add-selection', name)
        else: 
            self.ui_comm.send_user_error(f'no selection on {df_name} yet')


__all__ = ['Midas']
