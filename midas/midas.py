from __future__ import absolute_import
from IPython import get_ipython  # type: ignore
from typing import Optional, Union
from datascience import Table
# from pyperclip import copy

try:
    from IPython.display import display  # type: ignore
except ImportError as err:
    print("not in Notebook environment")
    display = lambda x: None
    logging = lambda x, y: None

from .stream import MidasSelectionStream

from .midas_algebra.dataframe import MidasDataFrame, DFInfo, RuntimeFunctions
from midas.state_types import DFName
from midas.event_types import TickItem
from .state import State
from .ui_comm import UiComm
from .midas_algebra.context import Context
from .midas_magic import MidasMagic
from .util.instructions import HELP_INSTRUCTION
from .util.errors import UserError, logging, check_not_null
from .util.utils import isnotebook, find_name

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
    shelf_selections: dict #TODO Change
    rt_funcs: RuntimeFunctions

    def __init__(self):
        # self.is_processing_tick: bool = False
        # FIXME: have a better mock up experience for testing, if we are not in notebook...
        # check if we are in a ipython environment
        ui_comm = UiComm(is_in_ipynb, self.add_selection)
        self.ui_comm = ui_comm
        self.shelf_selections = {}
        self.state = State(ui_comm)
        self.context = Context(self.state.dfs)
        self.event_loop = EventLoop(self.state)
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
        print("new column!")
        print(labels_and_values)
        table = Table().with_columns(*labels_and_values, **formatter)
        df_name = find_name()
        return MidasDataFrame.create_with_table(table, df_name, self.rt_funcs)


    # def register_df(self, df_name_raw: str, df_raw: DataFrame) -> MidasDataFrame:
    #     """we will add this both to state
    #        and to render
    #     """
    #     df_name = DFName(df_name_raw)
    #     logging("register_df", df_name)
    #     # FIXME: need to figure out where to propate df_name...
    #     df = MidasDataFrame.from_data(df_raw, df_name, self.rt_funcs)
    #     # TOTAL HACK
    #     globals()[df_name_raw] = df
    #     # self.state.add_df(df, True)
    #     # retuns
    #     return df

    # TODO: fix!!! we'd have to add this to the event loop
    # def link(self, df_interact: MidasDataFrame, df_update: MidasDataFrame):
    #     if (df_interact.df_name is None) or (df_update.df_name is None):
    #         # send error
    #         self.ui_comm.send_user_error("The DFs you wish to link must both have been assigned")
    #         return
    #     # basically replace the data in the tick cycles, while keeping the same name
    #     def transformation(predicate):
    #         df_update.apply_selection(predicate).show(df_update.df_name)
    #         return
    #     self.bind(df_interact.df_name, transformation)
    #     return


    def refresh_comm(self):
        self.ui_comm.set_comm()


    def _eval(self, code: str):
        # ran here because it has the correct scope
        return eval(code)


    def has_df(self, df_name_raw: str):
        return self.state.has_df(DFName(df_name_raw))


    # def register_series(self, series: Series, name: str):
    #     # turn it into a df
    #     df = series.to_frame()
    #     return self.register_df(name, df)


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

    # the re
    def get_df_info(self, df_name: DFName) -> Optional[DFInfo]:
        return self.state.dfs.get(df_name)


    def get_df_vis_info(self, df_name: str):
        return self.ui_comm.vis_spec.get(DFName(df_name))


    @staticmethod
    def help():
        print(HELP_INSTRUCTION)


    def add_selection(self, df_name_raw: str, selection: str):
        df_name = DFName(df_name_raw)
        # note that the selection is str because 
        logging("add_selection", df_name)
        # FIXME make sure this null checking is correct
        predicate = self.ui_comm.get_predicate_info(df_name, selection)
        self.event_loop.tick(predicate)
        return

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
