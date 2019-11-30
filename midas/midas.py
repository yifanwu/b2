from __future__ import absolute_import
from datetime import datetime
from IPython import get_ipython
from typing import Optional, Union, List, Dict, cast
from datascience import Table

try:
    from IPython.display import display  # type: ignore
except ImportError as err:
    print("not in Notebook environment")
    display = lambda x: None
    logging = lambda x, y: None

from .stream import MidasSelectionStream
from datetime import datetime
from typing import Dict, List

from .midas_algebra.dataframe import MidasDataFrame, DFInfo, VisualizedDFInfo
from .util.errors import InternalLogicalError, debug_log, type_check_with_warning
from .vis_types import SelectionEvent
from .state_types import DFName
from .ui_comm import UiComm
from midas.midas_algebra.dataframe import MidasDataFrame, DFInfo, JoinInfo, RuntimeFunctions, RelationalOp, VisualizedDFInfo
from midas.midas_algebra.context import Context

from midas.vis_types import SelectionEvent
from midas.state_types import DFName
from midas.event_types import TickItem
# from .state import State
from .ui_comm import UiComm
from .midas_magic import MidasMagic
from .util.instructions import HELP_INSTRUCTION
from .util.errors import UserError, logging, check_not_null
from .util.utils import isnotebook, find_name
from .config import default_midas_config, MidasConfig
from .event_loop import EventLoop


is_in_ipynb = isnotebook()


class Midas(object):
    """[summary]
    The Midas object holds the environment that controls different dataframes
    """
    magic: MidasMagic
    ui_comm: UiComm
    context: Context
    rt_funcs: RuntimeFunctions
    current_selection: Dict[DFName, SelectionEvent]
    assigned_name: str
    dfs: Dict[DFName, DFInfo]

    def __init__(self, config: MidasConfig=default_midas_config):
        # check the assigned name, if it is not 'm', then complain
        assigned_name = find_name(True)
        if assigned_name is None:
            raise UserError("must assign a name")
        self.assigned_name = assigned_name
        # TODO: the organization here is still a little ugly
        ui_comm = UiComm(is_in_ipynb, assigned_name, self.get_df)
        self.ui_comm = ui_comm
        self.dfs = {}
        self.context = Context(self.dfs, self.from_ops)
        self.event_loop = EventLoop(self.context, self.dfs, config)
        self.current_selection = {}
        if is_in_ipynb:
            ip = get_ipython()
            magics = MidasMagic(ip, ui_comm)
            ip.register_magics(magics)

        self.rt_funcs = RuntimeFunctions(
            self.add_df,
            self.show_df,
            self.get_stream,
            self.context.apply_selection,
            self.add_join_info)

    def add_df(self, mdf: MidasDataFrame):
        if mdf.df_name is None:
            raise InternalLogicalError("df should have a name to be updated")
        debug_log(f"+ Addign df {mdf.df_name}")
        self.dfs[mdf.df_name] = DFInfo(mdf)


    # 

    def show_df(self, mdf: MidasDataFrame, chart_config):
        if mdf.df_name is None:
            raise InternalLogicalError("df should have a name to be updated")
        # if it already exists
        if mdf.df_name in self.dfs:
            found_df = self.dfs[mdf.df_name]
            if isinstance(found_df, VisualizedDFInfo):
                found_df.update_df(mdf)
                # also 
                self.ui_comm.update_chart(mdf)
                self.ui_comm.navigate_to_chart(mdf.df_name)
            else:
                is_visualized = False
                if chart_config.is_base_df:
                    self.ui_comm.create_profile(mdf)
                is_visualized = self.ui_comm.visualize(mdf)
                if is_visualized:
                    self.dfs[mdf.df_name] = VisualizedDFInfo(mdf)
                # else, we don't do anything
            return


    def has_df(self, df_name: DFName):
        return df_name in self.dfs


    def append_df_predicates(self, selection: SelectionEvent) -> DFInfo:
        df_name = selection.df_name
        df_info = self.dfs.get(df_name)
        # idx = len(df_info.predicates)
        if df_info and isinstance(df_info, VisualizedDFInfo):
            df_info.predicates.append(selection)
            return df_info
        else:
            raise InternalLogicalError(f"Df ({df_name}) should be defined and be visualized as a chart!")


    def get_df(self, df_name: DFName):
        return self.dfs.get(df_name)


    def remove_df(self, df_name: DFName):
        self.dfs.pop(df_name)

    def from_records(self, records):
        table = Table.from_records(records)
        df_name = find_name()
        return MidasDataFrame.create_with_table(table, df_name, self.rt_funcs)


    def read_table(self, filepath_or_buffer, *args, **vargs):
        table = Table.read_table(filepath_or_buffer, *args, **vargs)
        df_name = find_name()
        return MidasDataFrame.create_with_table(table, df_name, self.rt_funcs)


    def from_df(self, df):
        # take a pandas df
        table = Table.from_df(df)
        df_name = find_name()
        return MidasDataFrame.create_with_table(table, df_name, self.rt_funcs)


    def from_ops(self, ops: RelationalOp):
        return MidasDataFrame(ops, self.rt_funcs)

    # def bin(self, column: str, ranges):
    #     # returns with new columsn `col_name_bin` and 
    #     return 

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
        df_info = cast(VisualizedDFInfo, self.get_df_info(df_name))
        check_not_null(df_info)

        return MidasSelectionStream(df_name, df_info.predicates, self.bind)


    def add_join_info(self, join_info: JoinInfo):
        self.context.add_join_info(join_info)
            

    def refresh_comm(self):
        self.ui_comm.set_comm(self.assigned_name)

    # the re
    def get_df_info(self, df_name: DFName) -> Optional[DFInfo]:
        return self.dfs.get(df_name)


    def get_df_vis_info(self, df_name: str):
        return self.ui_comm.vis_spec.get(DFName(df_name))


    @staticmethod
    def help():
        print(HELP_INSTRUCTION)


    def add_selection_by_interaction(self, df_name_raw: str, value):
        df_name = DFName(df_name_raw)
        predicate = self.ui_comm.get_predicate_info(df_name, value)
        date = datetime.now()
        selection_event = SelectionEvent(date, predicate, DFName(df_name))
        self.add_selection(selection_event)


    def add_selection(self, selection: SelectionEvent):
        # logging("add_selection", df_name)
        self.append_df_predicates(selection)
        self.current_selection[selection.df_name] = selection
        self.event_loop.tick(selection.df_name, selection, self.current_selection)
        return


    def bind(self, df_name: DFName, cb):
        item = TickItem(df_name, cb)
        return self.event_loop.add_callback(item)


    def add_facet(self, df_name: str, facet_column: str):
        # 
        raise NotImplementedError()
    


    # def js_get_current_chart_code(self, df_name_raw: str) -> Optional[str]:
    #     # figure out how to derive the current df
    #     # don't have a story yet for complicated things...
    #     # decide on if we want to focus on complex code gen...
    #     return


__all__ = ['Midas']
