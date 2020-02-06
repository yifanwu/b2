from __future__ import absolute_import
from midas.constants import LOG_FILE_HEADER
from midas.midas_algebra.selection import SelectionValue, ColumnRef, EmptySelection, SelectionType
from IPython import get_ipython
from typing import Optional, List, Dict, Iterator, IO, cast, Any
from datascience import Table
from json import dumps
from datetime import datetime
import os.path

try:
    from IPython.display import display  # type: ignore
except ImportError as err:
    print("not in Notebook environment")
    display = lambda x: None
    logging = lambda x, y: None

from typing import Dict, List

from .midas_algebra.dataframe import MidasDataFrame, DFInfo, VisualizedDFInfo, get_midas_code
from .util.errors import InternalLogicalError
from .util.utils import red_print
from .vis_types import SelectionEvent, EncodingSpec
from .state_types import DFName
from .ui_comm import UiComm
from midas.midas_algebra.dataframe import MidasDataFrame, DFInfo, JoinInfo, RuntimeFunctions, RelationalOp, VisualizedDFInfo
from midas.midas_algebra.context import Context

from midas.vis_types import SelectionEvent
from midas.state_types import DFName
from .ui_comm import UiComm
from .midas_magic import MidasMagic
from .util.instructions import HELP_INSTRUCTION
from .util.errors import UserError
from .util.utils import isnotebook, find_name, diff_selection_value
from .config import MidasConfig


is_in_ipynb = isnotebook()


class Midas(object):
    """[summary]
    The Midas object holds the environment that controls different dataframes
    convention:
      * a single "_" means that it's accesssed by JS facing features
      * two "_" means that it's accessed by other Py functions
    """
    magic: MidasMagic
    ui_comm: UiComm
    context: Context
    rt_funcs: RuntimeFunctions
    current_selection: List[SelectionValue]
    selection_history: List[List[SelectionValue]]
    assigned_name: str
    df_info_store: Dict[DFName, DFInfo]
    config: MidasConfig
    last_add_selection_df: str
    log_file: IO[Any]
    start_time: datetime

    def __init__(self, experiment_id: Optional[str]=None, linked=True):
        assigned_name = find_name(True)
        if assigned_name is None:
            raise UserError("must assign a name")
        self.assigned_name = assigned_name
        if experiment_id:
            dt = datetime.now()
            file_name = f'{experiment_id}_{dt.strftime("%Y%m%d-%H%M%S")}.csv'
            self.start_time = dt
            if os.path.isfile(file_name):
                raise InternalLogicalError(f"File {file_name} already existis, strange!")
            else:
                self.log_file = open(f"../experiment_results/{file_name}", 'w+')
                self.log_file.write(LOG_FILE_HEADER)
        ui_comm = UiComm(is_in_ipynb, assigned_name, self.__get_df_info, self.remove_df, self.from_ops, self._add_selection, self._get_filtered_code, self.log_entry)
        self.ui_comm = ui_comm
        self.df_info_store = {}
        self.context = Context(self.df_info_store, self.from_ops)
        self.selection_history = []
        self.config = MidasConfig(linked, True if experiment_id else False)
        self.last_add_selection_df = ""
        self.current_selection = []
        if is_in_ipynb:
            ip = get_ipython()
            magics = MidasMagic(ip, ui_comm)
            ip.register_magics(magics)


        self.rt_funcs = RuntimeFunctions(
            self.add_df,
            self._show_df,
            self._show_df_filtered,
            self.show_profile,
            self.context.apply_selection,
            self.add_join_info)


    def add_df(self, mdf: MidasDataFrame):
        if mdf.df_name is None:
            raise InternalLogicalError("df should have a name to be updated")
        self.df_info_store[mdf.df_name] = DFInfo(mdf)


    def show_profile(self, mdf: MidasDataFrame):
        self.ui_comm.create_profile(mdf)


    def _show_df_filtered(self, mdf: Optional[MidasDataFrame], df_name: DFName):
        if not self.__has_df(df_name):
            raise InternalLogicalError("cannot add filter to charts not created")
        self.ui_comm.update_chart_filtered_value(mdf, df_name)
        self.df_info_store[df_name].update_df(mdf)


    def _show_df(self, mdf: MidasDataFrame, spec: EncodingSpec):
        self.log_entry("show_df", mdf.df_name)
        if mdf.df_name is None:
            raise InternalLogicalError("df should have a name to be updated")
        df_name = mdf.df_name
        # if this visualization has existed, we must remove the existing interactions
        # the equivalent of updating the selection with empty
        if self.__has_df_chart(mdf.df_name):
            self._add_selection([EmptySelection(ColumnRef(spec.x, df_name))])
        self.df_info_store[df_name] = VisualizedDFInfo(mdf)
        self.ui_comm.create_chart(mdf, spec)
        # now we need to see if we need to apply selection,
        if len(self.current_selection) > 0:
            new_df = mdf.apply_selection(self.current_selection)
            new_df.filter_chart(df_name)


    def __has_df_chart(self, df_name: DFName):
        return df_name in self.df_info_store and isinstance(self.df_info_store[df_name], VisualizedDFInfo)


    def __has_df(self, df_name: DFName):
        return df_name in self.df_info_store

    def __get_df_info(self, df_name: str):
        return self.df_info_store.get(DFName(df_name))


    def __get_df(self, df_name: str):
        r = self.__get_df_info(df_name)
        if r:
            return r.df
        return None

    def log_entry(self, fun_name: str, optional_metadata: Optional[str]=None):
        """
        the structure would be 
        |  fun_name | call_time | 
        """
        if self.config.logging:
            call_time = datetime.now()
            diff = (call_time - self.start_time).total_seconds()
            self.log_file.write(f"{fun_name},{diff},{optional_metadata}\n")
            # This is important because the participant might restart kernel etc without warning.
            self.log_file.flush()

    # def download_log(self):
    #     ui_logs = []
    #     for item in self.ui_comm.logged_comms:
    #         # this is extremely brittle
    #         fun_name = item[4]
    #         call_time = item[5]
    #         ui_logs.append(f"{fun_name}, {call_time}")
    #     return "\n".join(ui_logs)


    def remove_df(self, df_name: DFName):
        self.df_info_store.pop(df_name)


    def from_records(self, records):
        table = Table.from_records(records)
        df_name = find_name()
        self.log_entry("load_data", df_name)
        return MidasDataFrame.create_with_table(table, df_name, self.rt_funcs)


    def read_table(self, filepath_or_buffer, *args, **vargs):
        try:
            table = Table.read_table(filepath_or_buffer, *args, **vargs)
            df_name = find_name()
            self.log_entry("load_data", df_name)
            return MidasDataFrame.create_with_table(table, df_name, self.rt_funcs)
        except FileNotFoundError:
            red_print(f"File {filepath_or_buffer} does not exist!")
        except UserError as err:
            red_print(err)


    def from_df(self, df):
        # a pandas df
        table = Table.from_df(df)
        df_name = find_name()
        self.log_entry("load_data", df_name)
        return MidasDataFrame.create_with_table(table, df_name, self.rt_funcs)


    def from_ops(self, ops: RelationalOp):
        return MidasDataFrame(ops, self.rt_funcs)


    def with_columns(self, *labels_and_values, **formatter):
        table = Table().with_columns(*labels_and_values, **formatter)
        df_name = find_name()
        self.log_entry("load_data", df_name)
        return MidasDataFrame.create_with_table(table, df_name, self.rt_funcs)


    def add_join_info(self, join_info: JoinInfo):
        self.log_entry("add_join_info")
        self.context.add_join_info(join_info)


    def _get_df_vis_info(self, df_name: str):
        return self.ui_comm.vis_spec.get(DFName(df_name))


    @staticmethod
    def help():
        print(HELP_INSTRUCTION)


    def get_current_selection(self):
        self.log_entry("get_current_selection")
        return self.current_selection


    # this function just modifies the current selection and returns it
    # this currently assume that all the selectionvalue are from one dataframe
    def _add_selection(self, selection: List[SelectionValue]) -> List[SelectionValue]:
        df_name = DFName(selection[0].column.df_name)
        # date = datetime.now()
        # selection_event = SelectionEvent(date, selection, DFName(df_name))
        # self.append_df_predicates(selection_event)
        new_selection = list(filter(lambda v: v.column.df_name != df_name, self.current_selection))
        none_empty = list(filter(lambda s: s.selection_type != SelectionType.empty , selection))
        new_selection.extend(none_empty)
        self.current_selection = new_selection
        return self.current_selection


    def __tick(self, all_predicate: Optional[List[SelectionValue]]=None):
        if all_predicate is None:
            # reset every df's filter
            for df_info in self.__get_visualized_df_info():
                self._show_df_filtered(None, df_info.df_name)
        else:
            if self.config.linked:
                # debug_log("here are your predicates")
                # print(all_predicate)
                for df_info in self.__get_visualized_df_info():
                    s = list(filter(lambda p: p.column.df_name != df_info.df_name, all_predicate))
                    if len(s) > 0:
                        new_df = df_info.original_df.apply_selection(s)
                        # debug_log(f"Filtering df {a_df_name}")
                        new_df.filter_chart(df_info.df_name)


    def __get_visualized_df_info(self) -> Iterator[VisualizedDFInfo]:
        for df_name in list(self.df_info_store):
            df_info = self.df_info_store[df_name]
            if isinstance(df_info, VisualizedDFInfo):
                yield df_info


    # PUBLIC
    def make_selections(self, current_selections_array: List[Dict]):
        """this function is executed via python cells
        this function makes idempotentn modifications to state
        Keyword Arguments:
            current_selections_array {Optional[List[Dict]]} --
            note that the dict is Dict[DFName, SelectionValue] (default: {None})
        """
        self.log_entry("code_selection", f"'{dumps(current_selections_array)}'")
        df_involved = ""
        if len(current_selections_array) == 0:
            # this is a reset!
            self.current_selection = []
            self.__tick()
        else:
            current_selection = []
            for v in current_selections_array:
                current_selection.extend(self.ui_comm.get_predicate_info(v)[0])

            # this check if for when there is no UI effect, but code effect
            diff = diff_selection_value(current_selection, self.current_selection)
            if len(diff) > 0:
                # either no change, or that
                # if there is only one diff, then we trigger with specific df
                dfs = set([d.column.df_name for d in diff])
                # debug_log("changed")
                df_involved = dfs.pop()
                self.current_selection = current_selection
            else:
                df_involved = self.last_add_selection_df
            self.__tick(current_selection)

        self.ui_comm.after_selection(current_selections_array, df_involved, len(self.selection_history))
        self.selection_history.append(self.current_selection)


    def _get_filtered_code(self, df_name: str):
        df = self.__get_df(df_name)
        if df is None or df.table is None:
            return self._get_original_code(df_name)
        else:
            return get_midas_code(df.ops)


    def _get_original_code(self, df_name: str):
        df_info = self.__get_df_info(df_name)
        if type(df_info) == VisualizedDFInfo:
            visualized_df_info = cast(VisualizedDFInfo, df_info)
            return get_midas_code(visualized_df_info.original_df.ops)
        else:
            raise InternalLogicalError(f"{df_name} is not visualized")


__all__ = ['Midas']
