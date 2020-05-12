from __future__ import absolute_import
from warnings import filterwarnings
from IPython import get_ipython
from typing import Optional, List, Dict, Iterator, Union, cast, Dict, List
from datascience import Table
from datascience.predicates import are
import numpy as np
import math
from json import dumps

from IPython.core.debugger import set_trace

try:
    from IPython.display import display  # type: ignore
except ImportError as err:
    print("not in Notebook environment")
    display = lambda x: None
    logging = lambda x, y: None

from midas.constants import ISDEBUG
from midas.midas_algebra.selection import SelectionValue, ColumnRef, EmptySelection, SelectionType, find_selections_with_df_name
from .midas_algebra.dataframe import MidasDataFrame, DFInfo, VisualizedDFInfo, get_midas_code
from .util.errors import InternalLogicalError, UserError
from .util.utils import red_print, isnotebook, find_name
from .vis_types import EncodingSpec
from .state_types import DFName
from .ui_comm import UiComm
from midas.midas_algebra.dataframe import MidasDataFrame, DFInfo, JoinInfo, RuntimeFunctions, RelationalOp, VisualizedDFInfo
from midas.midas_algebra.context import Context

from midas.state_types import DFName
from .ui_comm import UiComm
from .midas_magic import MidasMagic
from .util.instructions import HELP_INSTRUCTION
from .config import MidasConfig


is_in_ipynb = isnotebook()


class B2(object):
    """[summary]
    The Midas object holds the environment that controls different dataframes
    convention:
      * a single "_" means that it's accesssed by JS facing features
      * two "_" means that it's accessed by other Py functions
    """
    _magic: MidasMagic
    _ui_comm: UiComm
    _context: Context
    _rt_funcs: RuntimeFunctions
    immediate_interaction_selection: List[SelectionValue]
    current_selection: List[SelectionValue]
    all_selections: List[List[SelectionValue]]
    _assigned_name: str
    df_info_store: Dict[DFName, DFInfo]
    config: MidasConfig


    def __init__(self, user_id: Optional[str]=None, task_id: Optional[str]=None):
        # wrap around the data science library so we can use it
        self.are = are
        self.np = np
        self.math = math

        # deepcopy triggers 
        filterwarnings("ignore")
        assigned_name = find_name(True)
        if assigned_name is None:
            raise UserError("must assign a name")
        self._assigned_name = assigned_name
        logger_id = ""
        if user_id and task_id:
            logger_id = user_id + "_"+ task_id
        
        self.config = MidasConfig(True)

        ui_comm = UiComm(
            is_in_ipynb,
            assigned_name,
            logger_id,
            self._i_get_df_info,
            self.remove_df,
            self.from_ops,
            self._add_selection,
            self._get_filtered_code,
        )
        self._ui_comm = ui_comm
        self.df_info_store = {}
        self._context = Context(self.df_info_store, self.from_ops)
        self.all_selections = []
        self.immediate_interaction_selection = []
        self.current_selection = []
        if is_in_ipynb:
            ip = get_ipython()
            magics = MidasMagic(ip, ui_comm)
            ip.register_magics(magics)


        self._rt_funcs = RuntimeFunctions(
            self._add_df,
            self.create_with_table_wrap,
            self._show_df,
            self._get_filtered_df,
            self._context.apply_selection,
            self.add_join_info,
        )


    def _add_df(self, mdf: MidasDataFrame):
        if mdf.df_name is None:
            raise InternalLogicalError("df should have a name to be updated")
        self.df_info_store[mdf.df_name] = DFInfo(mdf)


    def show_profile(self, mdf: MidasDataFrame, df_name:str=None):
        # sanity check
        if df_name:
            mdf.df_name = df_name
        if not mdf.df_name:
            red_print("Cannot create the profiler, please provide df_name as second argument")
            return
        if mdf.__len__() == 0:
            red_print("Cannot create profiler for empty dataframe---please check the value of the dataframe.")
            return

        self._ui_comm.create_profile(mdf)


    def _show_df_filtered(self, mdf: Optional[MidasDataFrame], df_name: DFName):
        if not self._i_has_df(df_name):
            raise InternalLogicalError("cannot add filter to charts not created")
        df_info = self.df_info_store[df_name]
        if isinstance(df_info, VisualizedDFInfo):
            di = cast(VisualizedDFInfo, df_info)
            di.update_df(mdf)
            di.original_df._set_current_filtered_data(mdf)
            # ntoe that this MUST HAPPEN AFTER the state has been set...
            # if ISDEBUG: set_trace()
            self._ui_comm.update_chart_filtered_value(mdf, df_name)
        else:
            raise InternalLogicalError("should not show filtered on df not visualized!")


    def _show_df(self, mdf: MidasDataFrame, spec: EncodingSpec, trigger_filter=True):
        if mdf.df_name is None:
            raise InternalLogicalError("df should have a name to be updated")
        df_name = mdf.df_name
        # if this visualization has existed, we must remove the existing interactions
        # the equivalent of updating the selection with empty
        if self._i_has_df_chart(mdf.df_name):
            # FIXMENOW & shoud share logic with the remove_df
            self._add_selection([EmptySelection(ColumnRef(spec.x, df_name))])
        self.df_info_store[df_name] = VisualizedDFInfo(mdf)
        self._ui_comm.create_chart(mdf, spec)
        # now we need to see if we need to apply selection,
        # need to know if this came from a reactive cell
        if trigger_filter and len(self.current_selection) > 0:
            new_df = mdf.apply_selection(self.current_selection)
            self._show_df_filtered(new_df, df_name)


    def _i_has_df_chart(self, df_name: DFName):
        return df_name in self.df_info_store and isinstance(self.df_info_store[df_name], VisualizedDFInfo)


    def _i_has_df(self, df_name: DFName):
        return df_name in self.df_info_store

    def _i_get_df_info(self, df_name: str):
        return self.df_info_store.get(DFName(df_name))


    def _i_get_df(self, df_name: str):
        r = self._i_get_df_info(df_name)
        if r:
            return r.df
        return None

    def _get_filtered_df(self, df_name: str):
        # if this is one of the charts, return its current filtered value
        r = self._i_get_df_info(df_name)
        if r:
            if r.df_type == "visualized":
                return r.df
            else:
                # if this is one of the _original_ data, then filter it...
                # need to apply filter...
                return r.df.apply_self_selection_value(self.current_selection)
        return None


    def remove_df(self, df_name: DFName):
        # we need to remove the selection as well
        # and also doing a tick
        # maybe also send a notificaition?
        # see if there is a selection
        selected_columns = find_selections_with_df_name(self.current_selection, df_name)
        if len(selected_columns) > 0:
            # then make a selection to remove things
            # make empty selection
            empty_sel = [EmptySelection(c) for c in selected_columns]            
            self._ui_comm.internal_current_selection(empty_sel, df_name) # type: ignore
        self.df_info_store.pop(df_name)

    def create_with_table_wrap(self, table, df_name):
        df = MidasDataFrame.create_with_table(table, df_name, self._rt_funcs)
        self.show_profile(df)
        return df


    def from_records(self, records):
        table = Table.from_records(records)
        df_name = find_name()
        return self.create_with_table_wrap(table, df_name)
        

    def from_file(self, filepath_or_buffer, *args, **vargs):
        try:
            table = Table.read_table(filepath_or_buffer, *args, **vargs)
            df_name = find_name()
            return self.create_with_table_wrap(table, df_name)
        except FileNotFoundError:
            red_print(f"File {filepath_or_buffer} does not exist!")
        except UserError as err:
            red_print(err)


    def from_df(self, df):
        # a pandas df
        table = Table.from_df(df)
        df_name = find_name()
        return self.create_with_table_wrap(table, df_name)


    def from_ops(self, ops: RelationalOp):
        return MidasDataFrame(ops, self._rt_funcs)


    def with_columns(self, *labels_and_values, **formatter):
        table = Table().with_columns(*labels_and_values, **formatter)
        df_name = find_name()
        return self.create_with_table_wrap(table, df_name)


    def add_join_info(self, join_info: JoinInfo):
        self._context.add_join_info(join_info)


    def _get_df_vis_info(self, df_name: str):
        return self._ui_comm.vis_spec.get(DFName(df_name))


    def help(self, fun = None):
        """pass in the function you want to learn about
        """
        if fun:
            if fun.__doc__:
                print(fun.__doc__)
            else:
                print("We are not able to find the documentation")
        else:
            print(HELP_INSTRUCTION)


    @property
    def immediate_interaction_value(self):
        """syntax shortcut for the first value selected
        - if it's a bar chart, it's array of string, e.g., ['CA']
        - if it's scatter or line, it's, e.g., [100, 200]
        """
        if len(self.immediate_interaction_selection) == 0:
            return None
        first = self.immediate_interaction_selection[0]
        if first.selection_type == SelectionType.empty:
            return None
        # if first.selection_type == SelectionType.string_set:
        return first.val # type: ignore

    # this function just modifies the current selection and returns it
    # this currently assume that all the selectionvalue are from one dataframe
    def _add_selection(self, selection: List[SelectionValue]) -> List[SelectionValue]:
        df_name = DFName(selection[0].column.df_name)
        # date = datetime.now()
        # selection_event = SelectionEvent(date, selection, DFName(df_name))
        # self.append_df_predicates(selection_event)
        self.immediate_interaction_selection = selection
        new_selection = list(filter(lambda v: v.column.df_name != df_name, self.current_selection))
        none_empty = list(filter(lambda s: s.selection_type != SelectionType.empty , selection))
        new_selection.extend(none_empty)
        self.current_selection = new_selection
        return self.current_selection


    def __tick(self, all_predicate: Optional[List[SelectionValue]]=None):
        if all_predicate is None:
            # reset every df's filter
            for df_info in self.__get_visualized_df_info():
                if df_info.df_name:
                    self._show_df_filtered(None, df_info.df_name)
                else:
                    raise InternalLogicalError("df must be named")
        else:
            if not self.config.linked:
                return

            for df_info in self.__get_visualized_df_info():
                s = list(filter(lambda p: p.column.df_name != df_info.df_name, all_predicate))
                if len(s) > 0:
                    new_df = df_info.original_df.apply_selection(s)
                    if df_info.df_name:
                        self._show_df_filtered(new_df, df_info.df_name)
                    else:
                        raise InternalLogicalError("df must be named")
                else:
                    # Note: we need to first clear the selections, otherwise filters that are not active won't happen.
                    self._show_df_filtered(None, df_info.df_name)



    def __get_visualized_df_info(self) -> Iterator[VisualizedDFInfo]:
        for df_name in list(self.df_info_store):
            df_info = self.df_info_store[df_name]
            if isinstance(df_info, VisualizedDFInfo):
                yield df_info


    # PUBLIC
    def sel(self, current_selections_list: Union[List[Dict], List[SelectionValue]]=[]):
        """makes selections to visualizations in Midas pane
        
        Arguments:
            current_selections_list {Union[List[Dict], List[SelectionValue]]} -- a list of either (1) dictionaries that describes the chart of the selection and the selection, or 
            for example
            >>> m.sel([{"STATE_distribution": {"STATE": ["CA"]}}])
            >>> m.sel([]) # clear selections
            >>> m.sel(m.all_selections[-2]) # selects the second last selection you made in the past

        """
        df_involved = ""
        if len(current_selections_list) == 0:
            # this is a reset!
            self.current_selection = []
            self.__tick()
        else:
            # have to ignore because the type checker is dumb
            current_selection: List[SelectionValue] = []
            if type(current_selections_list[0]) == SelectionValue:
                current_selection = current_selections_list # type: ignore
            else:
                for v in current_selections_list:
                    # flatmap
                    current_selection.extend(self._ui_comm.get_predicate_info(v)[0]) # type: ignore
            # this check if for when there is no UI effect, but code effect
            # diff = diff_selection_value(current_selection, self.current_selection)
            # if len(diff) > 0:
            #     dfs = set([d.column.df_name for d in diff])
            #     # note that we ignore the case when multipel dataframes have changed.
            #     df_involved = dfs.pop()
            #     self.current_selection = current_selection
            # else:
            # note that we only trigger df_involved when it's from the GUI, and tht GUI sets the 
            self.current_selection = current_selection
            df_involved = ""
            if len(self.immediate_interaction_selection)> 0:
                df_involved = self.immediate_interaction_selection[0].column.df_name
            self.__tick(current_selection)

        self._ui_comm.after_selection(current_selections_list, df_involved, len(self.all_selections))
        self.all_selections.append(self.current_selection)
        return

    def log_start_task(self, task_id: str):
        self._ui_comm.log_start_task(task_id)

    def _get_filtered_code(self, df_name: str):
        df = self._i_get_df(df_name)
        if df is None or df.table is None:
            return self._get_original_code(df_name)
        else:
            return get_midas_code(df._ops, self._assigned_name)

        

    def _get_original_code(self, df_name: str):
        df_info = self._i_get_df_info(df_name)
        if type(df_info) == VisualizedDFInfo:
            visualized_df_info = cast(VisualizedDFInfo, df_info)
            return get_midas_code(visualized_df_info.original_df._ops, self._assigned_name)
        else:
            raise InternalLogicalError(f"{df_name} is not visualized")


__all__ = ['B2']
