from datetime import datetime
from midas.config import IS_DEBUG
from IPython import get_ipython 
from pandas.api.types import is_string_dtype, is_numeric_dtype, is_datetime64_any_dtype 
from ipykernel.comm import Comm # type: ignore
import numpy as np
# from json import loads
from typing import Dict, Callable, Optional, List, Tuple, Type, cast
import json
from pyperclip import copy
import ast
import functools
import inspect

# for development
from IPython.core.debugger import set_trace
from midas.constants import ISDEBUG

from midas.midas_algebra.data_types import DFId
from midas.midas_algebra.selection import SelectionValue
from .constants import MIDAS_CELL_COMM_NAME, MAX_BINS, MIDAS_RECOVERY_COMM_NAME, STUB_DISTRIBUTION_BIN
from midas.state_types import DFName
from midas.midas_algebra.dataframe import MidasDataFrame, RelationalOp, DFInfo, VisualizedDFInfo, get_midas_code
from midas.midas_algebra.selection import NumericRangeSelection, SetSelection, ColumnRef, EmptySelection
from .util.errors import InternalLogicalError, MockComm, debug_log, NotAllCaseHandledError
from .util.utils import sanitize_string_for_var_name
from .vis_types import EncodingSpec, FilterLabelOptions
from .util.data_processing import dataframe_to_dict, get_numeric_distribution_code, get_datetime_distribution_code, get_basic_group_vis

def logged(remove_on_chart_removal: bool):
    def wrapper_factory(f):
        @functools.wraps(f)
        def wrapper(self, *args, **kwargs):
            ret = f(self, *args, **kwargs)
            params = inspect.signature(f).parameters

            if remove_on_chart_removal and "df_name" in params:
                index = list(inspect.signature(f).parameters).index("df_name") - 1
                df_to_remove = args[index]
                assert isinstance(df_to_remove, str)
            elif remove_on_chart_removal and "df" in params:
                index = list(inspect.signature(f).parameters).index("df") - 1
                df_to_remove = args[index].df_name
                assert isinstance(df_to_remove, str)
            else:
                df_to_remove = None
            self.log(f, args, kwargs, df_to_remove)
            return ret
        return wrapper
    return wrapper_factory

class UiComm(object):
    comm: Comm
    recovery_comm: Comm
    vis_spec: Dict[DFName, EncodingSpec]
    id_by_df_name: Dict[DFName, DFId]
    is_in_ipynb: bool
    midas_instance_name: str
    create_df_from_ops:  Callable[[RelationalOp], MidasDataFrame]

    def __init__(self,
        is_in_ipynb: bool,
        midas_instance_name: str,
        logger_id: str,
        get_df_fun: Callable[[DFName], Optional[DFInfo]],
        remove_df_fun: Callable[[DFName], None],
        create_df_from_ops: Callable[[RelationalOp], MidasDataFrame],
        add_selection: Callable[[List[SelectionValue]], List[SelectionValue]],
        get_filtered_code: Callable[[str], str]):

        # functions passed at creation time
        self.is_in_ipynb = is_in_ipynb
        self.midas_instance_name = midas_instance_name
        self.set_comm(midas_instance_name, logger_id)
        self.register_recovery_comm(midas_instance_name, logger_id)
        self.get_df = get_df_fun
        self.remove_df_fun = remove_df_fun
        self.create_df_from_ops = create_df_from_ops
        self.add_selection = add_selection
        self.get_filtered_code = get_filtered_code

        # internal state
        self.next_id = 0
        self.vis_spec = {}
        self.id_by_df_name = {}
        self.shelf_selections = {}
        self.logged_comms = []
        self.tmp_log = []

    def log(self, function, args, kwargs, associated_df_name: str):
        self.logged_comms.append((
            function,           # 0
            args,               # 1
            kwargs,             # 2
            associated_df_name, # 3
        ))


    def run_log(self):
        for f, args, kwargs, _ in self.logged_comms:
          f(self, *args, *kwargs)

    def remove_df_from_log(self, df_name):
        def does_not_contain_df_name(entry):
            return entry[3] != df_name
        self.logged_comms = list(filter(does_not_contain_df_name, self.logged_comms))

    def handle_msg(self, data_raw):
        data = data_raw["content"]["data"]
        self.tmp_log.append(data)
        if "command" in data:
            command = data["command"]
            if command == "cell-ran":
                if "code" in data:
                    code = data["code"]
                return
            elif command == "markdown-cell-rendered":
                if "code" in data:
                    code = data["code"]
                return
            elif command == "get-visualization-code-clipboard":
                df_name = data["df_name"]
                encoding = self.vis_spec[df_name]
                code = f"{df_name}.vis({encoding.to_args})"
                copy(code)
                return
            elif command == "column-selected":
                column = data["column"]
                df_name = DFName(data["df_name"])
                self.tmp = f"{column}_{df_name}"
                code, execute, err_message = self.create_distribution_query(column, df_name)
                if code:
                    if execute:
                        # creating new line so that the horizontal scroll wouldn't occlude the code
                        self.create_cell(code, "query", True)
                    else:
                        self.send_column_click_error_msg(
                            f'We are not able to create a chart for {df_name}--{err_message}',
                            df_name,
                            column
                        )
                        self.create_cell(code, "query", False)
                return
            elif command == "remove-dataframe":
                df_name = data["df_name"]
                self.remove_df_fun(df_name)
                del self.vis_spec[df_name]
                self.remove_df_from_log(df_name)
                return
            elif command == "add_current_selection":
                value = json.loads(data["value"])
                # parse it first!
                s = data["value"]
                debug_log(f"add_current_selection {s}")
                self.handle_add_current_selection(value)
                return
            else:
                m = f"Command {command} not handled!"
                raise NotAllCaseHandledError(m)
        else:
            debug_log(f"Got message from JS Comm: {data}")


    def internal_current_selection(self, selections: List[SelectionValue], df_name):
        all_predicate = self.add_selection(selections)
        # now turn this into JSON
        param_str = "[]"
        if len(all_predicate) > 0:
            predicates = ", ".join(list(map(lambda v: v.to_str() if v.to_str() else "", all_predicate)))
            param_str = f"[{predicates}]"
        self.execute_selection(param_str, df_name)


    # note that this is extracted out for better debugging.
    def handle_add_current_selection(self, value: Dict):
        selections, df_name = self.get_predicate_info(value)
        self.internal_current_selection(selections, df_name)


    def set_comm(self, midas_instance_name: str, logger_id: str):
        if self.is_in_ipynb:
            self.comm = Comm(target_name = MIDAS_CELL_COMM_NAME)
            self.comm.send({
                "type": "initialize",
                "name": midas_instance_name,
                "loggerId": logger_id
            })
            self.comm.on_msg(self.handle_msg)
        else:
            self.comm = MockComm()


    def register_recovery_comm(self, midas_instance_name: str, logger_id: str):
        def target_func(comm, open_msg):
            # comm is the kernel Comm instance
            # msg is the comm_open message
        
            # Register handler for later messages
            @comm.on_msg
            def _recv(msg):
                if not self.logged_comms:
                    debug_log("Received recovery request, but nothing to recover, so no need to reopen comm.")
                    return
                else:
                    debug_log("Received recovery request. Reopening comm...")
                    self.set_comm(self.midas_instance_name, logger_id)
                    debug_log("Clearing stored visualizations...")
                    self.vis_spec = {}
                    debug_log("Comm reopened. Rerunning logged commands...")
                    self.run_log()
 
        # debug_log("Registering recovery comm...")
        get_ipython().kernel.comm_manager.register_target(MIDAS_RECOVERY_COMM_NAME, target_func)

    @logged(remove_on_chart_removal=False)
    def create_profile(self, df: MidasDataFrame):
        # debug_log(f"creating profile {df.df_name}")
        if df.df_name is None:
            raise InternalLogicalError("df should have a name to be updated")
        columns = [{"columnName": c.name, "columnType": c.c_type.value} for c in df.columns]
        # debug_log(f"Creating profile with columns {columns}")
        message = {
            "type": "profiler",
            "dfName": df.df_name,
            "columns": json.dumps(columns)
        }
        self.comm.send(message)
        return


    @logged(remove_on_chart_removal=True)
    def create_chart(self, df: MidasDataFrame, encoding: EncodingSpec):
        if df.df_name is None:
            raise InternalLogicalError("df should have a name to be updated")
        # first check if the encodings has changed, or if the data has changed.
        if df.df_name in self.vis_spec:
            if self.vis_spec[df.df_name] == encoding and self.id_by_df_name[df.df_name] == df._id:
                return

        self.vis_spec[df.df_name] = encoding
        self.id_by_df_name[df.df_name] = df._id

        # if ISDEBUG: set_trace()
        records = dataframe_to_dict(df, FilterLabelOptions.unfiltered)
        code = get_midas_code(df._ops, self.midas_instance_name)
        # TODO: check if we even need to do the dumping
        data = json.dumps(records)
        hash_val = df._id + "_" + encoding.to_hash()
        message = {
            'type': 'chart_render',
            "dfName": df.df_name,
            'encoding': encoding.to_json(),
            'data': data,
            'code': code,
            'hashVal': hash_val
        }
        self.comm.send(message)
        return
        

    def get_dfs_from_code_str(self, code: str) -> List[MidasDataFrame]:
        assignments = []
        class CustomNodeTransformer(ast.NodeTransformer):
            def visit_Assign(self, node):
                try:
                    assignments.append(node.targets[0].id)
                    return node
                except AttributeError:
                    return None
        # there are some magics that we should not parse
        # if they do have magics it should start in the first line
        if len(code) > 0 and code[0] == "%":
            debug_log(f"magic encountered for code {code}")
            return []
        nodes = ast.parse(code)
        CustomNodeTransformer().visit(nodes)
        assignements_str = ",".join(assignments)
        debug_log(f"Parsed {assignements_str}")

        df_assignments = []
        for a in assignments:
            r = self.get_df(DFName(a))
            if r is not None:
                df_assignments.append(r.df)
            else:
                debug_log(f"We cannot find {a} in current state")
        return df_assignments
    

    @logged(remove_on_chart_removal=True)
    def update_chart_filtered_value(self, df: Optional[MidasDataFrame], df_name: DFName):
        # note that this is alwsays used for updating filtered information
        if df_name not in self.vis_spec:
            raise InternalLogicalError(f"Cannot update df: {df_name}, since it was not visualized before")
        code = self.get_filtered_code(df_name)
        if df is None or df.table is None:
            self.comm.send({
                "type": "chart_update_data",
                "dfName": df_name,
                "newData": [],
                "code": code
            })
        else:
            new_data = dataframe_to_dict(df, FilterLabelOptions.filtered)
            self.comm.send({
                "type": "chart_update_data",
                "dfName": df_name,
                "newData": new_data,
                "code": code
            })
        return

    @logged(remove_on_chart_removal=True)
    def after_selection(self, selections, df_name, tick: int):
        self.comm.send({
            "type": "after_selection",
            "selection": json.dumps(selections),
            "dfName": df_name,
            "tick": tick
        })
        
    def create_cell(self, s, fun_kind: str, should_run: bool):
        # self.send_debug_msg(f"create_cell_with_text called {s}")
        # self.send_debug_msg(fcreating cell: {annotated}")
        self.comm.send({
            "type": "create_cell",
            "funKind": fun_kind,
            "code": s,
            "shouldRun": should_run
        })

    def remove_reactive_cell(self):
        self.comm.send({
            "type": "deactive",
        })

    # note that we do not need to provide the cellid
    #   that's information to be captured on the JS end.
    def add_reactive_cell(self, df_name: str):
    # , do_append: bool):
        self.comm.send({
            "type": "reactive",
            "dfName": df_name,
            # "appendFlag": 1 if do_append else 0
        })


    def execute_selection(self, params: str, df_name: str):
        self.comm.send({
            "type": "execute_selection",
            "params": params,
            "dfName": df_name,
        })

    def execute_fun(self, fun: str, params: str):
        self.comm.send({
            "type": "execute_fun",
            "funName": fun,
            "params": params,
        })

    def send_debug_msg(self, message: str):
        self.comm.send({
            "type": "notification",
            "style": "debug",
            "value": message
        })

    def send_column_click_error_msg(self, message: str, df_name: str, column_name: str):
        self.comm.send({
            "type": "notification",
            "style": "error",
            "value": message,
            "dfName": df_name,
            "columnName": column_name,
        })

    def log_start_task(self, task_id: str):
        self.comm.send({
            "type": "task-start",
            "value": task_id
        })
        print("Task logged", task_id)

    def get_predicate_info(self, selections: Dict) -> Tuple[List[SelectionValue], str]:
        """[summary]
        
        Arguments:
            selections {Dict} -- [description]
        
        Raises:
            InternalLogicalError: "if the selection is not in the format expected"
        
        Returns:
            Tuple[List[SelectionValue], str] -- [description]
        """
        # debug_log(f"selection is {selections}")
        if selections is None:
            raise InternalLogicalError("selection must be defined")
        keys = selections.keys()
        if len(keys) == 0:
            # return [], df_name
            raise InternalLogicalError("selection df must be defined")
        result = []
        if len(keys) != 1:
            raise InternalLogicalError("Expected one key for selection")
        df_name = list(keys)[0]
        selection = selections[df_name]
        # columns = list(column_selections.keys())
        vis = self.vis_spec[df_name]
        x = ColumnRef(vis.x, df_name)
        if not selection:
            if vis.selection_dimensions == "xy":
                y = ColumnRef(vis.y, df_name)
                result.extend([
                    EmptySelection(x),
                    EmptySelection(y)
                ])
            elif vis.selection_dimensions == "x":
                result.extend([
                    EmptySelection(x)
                ])
            elif vis.selection_dimensions == "y":
                y = ColumnRef(vis.y, df_name)
                result.extend([
                    EmptySelection(x)
                ])
        else:
            selections_added = 0
            if vis.x in selection:
                if vis.x_type == "quantitative" or vis.x_type == "temporal":
                    x_selection = NumericRangeSelection(x, selection[vis.x][0], selection[vis.x][1])
                else:
                    x_selection = SetSelection(ColumnRef(vis.x, df_name), selection[vis.x])
                result.append(x_selection)
                selections_added += 1
            if vis.y in selection:
                y = ColumnRef(vis.y, df_name)
                
                if vis.x_type == "quantitative" or vis.x_type == "temporal":
                    y_selection = NumericRangeSelection(y, selection[vis.y][0], selection[vis.y][1])
                else:
                    y_selection = SetSelection(ColumnRef(vis.y, df_name), selection[vis.x])
                result.append(y_selection)
                selections_added += 1
            if selections_added == 0:
                raise InternalLogicalError(f"Unknown selection {selection}");
        return result, df_name

    # @logged(remove_on_chart_removal=False, "update_selection_shelf_selection_name")
    # def update_selection_shelf_selection_name(self, old_name: str, new_name: str):
    #   self.shelf_selections[new_name] = self.shelf_selections[old_name]
    #   del self.shelf_selections[old_name]
    

    # @logged(remove_on_chart_removal=False)
    # def remove_selection_from_shelf(self, df_name: str):
    #   del self.shelf_selections[df_name]

    # returns a tuple to indicate if the retured result should be ran
    def create_distribution_query(self, col_name: str, df_name: str) -> Tuple[str, bool, str]:
        df_info = self.get_df(DFName(df_name))
        if df_info is None:
            raise InternalLogicalError("Should not be getting distribution on unregistered dataframes and columns")
        df = df_info.df
        col_value = df.table.column(col_name)
        new_name = sanitize_string_for_var_name(f"{col_name}_{df_name}_dist")
        if (is_string_dtype(col_value)):
            # we need to check the cardinarily
            code = get_basic_group_vis(new_name, df.df_name, col_name)
            try:
                unique_vals = np.unique(col_value)
            except TypeError:
                # with None value
                return (code, False, f"Please handle None values from {col_name}!")
            current_max_bins = len(unique_vals)
            if current_max_bins < MAX_BINS:
                return (code, True, "")
            else:
                # try parsing a value
                try:
                    parsed = col_value.astype('datetime64')
                    return get_datetime_distribution_code(col_name, df)
                except ValueError:
                    # too many columns
                    return (code, False, f"Too many columns to display for column {col_name}!")
        else:
            # we need to write the binning function and then print it out...
            # get the bound
            unique_vals = np.unique(col_value[~np.isnan(col_value)])
            current_max_bins = len(unique_vals)
            if (current_max_bins < MAX_BINS):
                code = get_basic_group_vis(new_name, df.df_name, col_name)
                return (code, True, "")
            else:
                return get_numeric_distribution_code(current_max_bins, unique_vals, col_name, df.df_name, new_name, self.midas_instance_name)
            

            
