from midas.midas_algebra.data_types import DFId
from IPython import get_ipython 
from pandas.api.types import is_string_dtype, is_numeric_dtype, is_datetime64_any_dtype 
from midas.midas_algebra.selection import SelectionValue
from ipykernel.comm import Comm # type: ignore
import numpy as np
# from json import loads
from typing import Dict, Callable, Optional, List
import json
from pyperclip import copy
import ast

from .constants import MIDAS_CELL_COMM_NAME, MAX_BINS, MIDAS_RECOVERY_COMM_NAME
from midas.state_types import DFName

from midas.midas_algebra.dataframe import MidasDataFrame, RelationalOp, DFInfo
from midas.midas_algebra.selection import NumericRangeSelection, SetSelection, ColumnRef, EmptySelection
from .util.errors import InternalLogicalError, MockComm, debug_log, NotAllCaseHandledError
from .vis_types import EncodingSpec, FilterLabelOptions
from .util.data_processing import dataframe_to_dict, snap_to_nice_number
import functools
import inspect
from midas.showme import infer_encoding

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

    def __init__(self, is_in_ipynb: bool, midas_instance_name: str,
      get_df_fun: Callable[[DFName], Optional[DFInfo]],
      remove_df_fun: Callable[[DFName], None],
      create_df_from_ops: Callable[[RelationalOp], MidasDataFrame],
      add_selection: Callable[[List[SelectionValue]], List[SelectionValue]],
      get_filtered_code: Callable[[str], str]):

        # functions passed at creation time
        self.is_in_ipynb = is_in_ipynb
        self.midas_instance_name = midas_instance_name
        self.set_comm(midas_instance_name)
        self.register_recovery_comm(midas_instance_name)
        self.get_df = get_df_fun
        self.remove_df_fun = remove_df_fun
        self.create_df_from_ops = create_df_from_ops
        self.add_selection = add_selection
        self.get_filtered_code = get_filtered_code\

        # internal state
        self.next_id = 0
        self.vis_spec = {}
        self.id_by_df_name = {}
        self.shelf_selections = {}
        self.logged_comms = []
        self.tmp_log = []

    def log(self, function, args, kwargs, associated_df_name):
        self.logged_comms.append((function, args, kwargs, associated_df_name))

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
        debug_log(f"got message {data}")
        if "command" in data:
            command = data["command"]
            if command == "cell-ran":
                if "code" in data:
                    code = data["code"]
                    self.process_code(code)
                return
            elif command == "get_code_clipboard":
                df_name = data["df_name"]
                code = self.get_filtered_code(df_name)
                # self.send_debug_msg(f"got code for {df_name}: {code}")
                copy(code)
                return
            elif command == "get_visualization_code_clipboard":
                df_name = data["df_name"]
                encoding = self.vis_spec[df_name]
                encoding_arg = f"mark='{encoding.mark}', x='{encoding.x}', y='{encoding.y}'"
                code = f"{df_name}.show({encoding_arg})"
                # self.send_debug_msg(f"got code for {df_name}: {code}")
                copy(code)
            elif command == "column-selected":
                # self.send_debug_msg("column-selected called")
                column = data["column"]
                df_name = DFName(data["df_name"])
                self.tmp = f"{column}_{df_name}"
                code = self.create_distribution_query(column, df_name)
                self.create_then_execute_cell(code, "query")
                # now we need to figure out what kind of transformation is needed
                # if nothing, we just show the table
            elif command == "remove_dataframe":
                df_name = data["df_name"]
                self.remove_df_fun(df_name)
                # local store
                del self.vis_spec[df_name]
                self.remove_df_from_log(df_name)

            elif command == "add_current_selection":
                value = json.loads(data["value"])
                # parse it first!
                # self.send_debug_msg(f"got add_current_selection message {value}")
                self.handle_add_current_selection(value)
            else:
                m = f"Command {command} not handled!"
                # self.send_debug_msg(m)
                raise NotAllCaseHandledError(m)
        else:
            debug_log(f"Got message from JS Comm: {data}")


    # note that this is extracted out for better debugging.
    def handle_add_current_selection(self, value: Dict):
        selections = self.get_predicate_info(value)
        all_predicate = self.add_selection(selections)
        # now turn this into JSON
        param_str = "[]"
        if len(all_predicate) > 0:
            predicates = ",".join(list(map(lambda v: v.to_str(), all_predicate)))
            param_str = f"[{predicates}]"
        # self.send_debug_msg(f"creating code\n{code}")
        self.execute_fun("make_selections", param_str)


    def process_code(self, code: str):
        assigned_dfs = self.get_dfs_from_code_str(code)
        if len(assigned_dfs) == 0:
            # do nothing
            debug_log("no df to process")
            return
        # code_lines = []
        for df in assigned_dfs:
            if df.is_base_df:
                # just execute it! since there is no configuration
                df.show_profile()
            else:
                encoding = infer_encoding(df)
                df.show(mark=encoding.mark, x=encoding.x, y=encoding.y)


    def set_comm(self, midas_instance_name: str):
        if self.is_in_ipynb:
            self.comm = Comm(target_name = MIDAS_CELL_COMM_NAME)
            # tell the JS side what the assigned name is
            self.comm.send({
                "type": "midas_instance_name",
                "value": midas_instance_name
            })
            self.comm.on_msg(self.handle_msg)
        else:
            self.comm = MockComm()


    def register_recovery_comm(self, midas_instance_name: str):
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
                    self.set_comm(self.midas_instance_name)
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
        # debug_log(f"creating chart {mdf.df_name}")
        if df.df_name is None:
            raise InternalLogicalError("df should have a name to be updated")
        # first check if the encodings has changed
        if df.df_name in self.vis_spec:
            if self.vis_spec[df.df_name] == encoding and self.id_by_df_name[df.df_name] == df.id:
                # no op
                # debug_log("no op, same stuff")
                return

        self.vis_spec[df.df_name] = encoding
        self.id_by_df_name[df.df_name] = df.id

        # vega_lite = gen_spec(mdf.df_name, encoding)
        records = dataframe_to_dict(df, FilterLabelOptions.unfiltered)
        # TODO: check if we even need to do the dumping
        data = json.dumps(records)
        message = {
            'type': 'chart_render',
            "dfName": df.df_name,
            'encoding': encoding.to_json(),
            'data': data,
        }
        self.comm.send(message)
        return


    def get_dfs_from_code_str(self, code: str) -> List[MidasDataFrame]:
        assignments = []
        class CustomNodeTransformer(ast.NodeTransformer):
            def visit_Assign(self, node):
                assignments.append(node.targets[0].id)
                return node
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
        if df is None or df.table is None:
            self.comm.send({
                "type": "chart_update_data",
                "dfName": df_name,
                "newData": []
            })
        else:
            new_data = dataframe_to_dict(df, FilterLabelOptions.filtered)
            self.comm.send({
                "type": "chart_update_data",
                "dfName": df_name,
                "newData": new_data
            })
        return


    def send_user_error(self, message: str):
        self.comm.send({
            "type": "notification",
            "style": "error",
            "value": message
        })

    def add_selection_to_shelf(self, selections):
        self.comm.send({
            "type": "add_selection_to_shelf",
            "value": json.dumps(selections)
        })
        
    def create_then_execute_cell(self, s, funKind):
        # self.send_debug_msg(f"create_cell_with_text called {s}")
        # self.send_debug_msg(f"creating cell: {annotated}")
        self.comm.send({
            "type": "create_then_execute_cell",
            "funKind": funKind,
            "code": s
        })

    # note that we do not need to provide the cellid
    #   that's information to be captured on the JS end.
    def add_reactive_cell(self, df_name):
        self.comm.send({
            "type": "reactive",
            "value": df_name
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

    def navigate_to_chart(self, df_name: DFName):
        self.comm.send({
            "type": "navigate_to_vis",
            "value": df_name
        })

    # this is assumed to be the selection on only one chart
    def get_predicate_info(self, selections: Dict) -> List[SelectionValue]:
        # debug_log(f"selection is {selections}")
        keys = selections.keys()
        if selections is None or len(keys) == 0:
            return []
        result = []
        if len(keys) != 1:
            raise InternalLogicalError("Expected one key for selection")
        df_name = list(keys)[0]
        selection = selections[df_name]
        # columns = list(column_selections.keys())
        vis = self.vis_spec[df_name]
        x = ColumnRef(vis.x, df_name)
        if not selection:
            if vis.mark == "circle":
                y = ColumnRef(vis.y, df_name)
                result.extend([
                    EmptySelection(x),
                    EmptySelection(y)
                ])
            else:
                result.extend([
                    EmptySelection(x)
                ])
        else:
            if vis.mark == "circle":
                y = ColumnRef(vis.y, df_name)
                # the predicate is either going to be x or y, or both
                selections_added = 0
                if vis.x in selection:
                    x_selection = NumericRangeSelection(x, selection[vis.x][0], selection[vis.x][1])
                    result.append(x_selection)
                    selections_added += 1
                if vis.y in selection:
                    y_selection = NumericRangeSelection(y, selection[vis.y][0], selection[vis.y][1])
                    result.append(y_selection)
                    selections_added += 1
                if selections_added == 0:
                    raise InternalLogicalError(f"Unknown selection {selection}");
            elif vis.mark == "bar":
                predicate = SetSelection(ColumnRef(vis.x, df_name), selection[vis.x])
                result.append(predicate)
            elif vis.mark == "line":
                x_selection = NumericRangeSelection(ColumnRef(vis.x, df_name), selection[vis.x][0], selection[vis.x][1])
                result.append(x_selection)
            else:
                raise InternalLogicalError(f"{vis.mark} not handled")
        return result

    @logged(remove_on_chart_removal=False)
    def update_selection_shelf_selection_name(self, old_name: str, new_name: str):
      self.shelf_selections[new_name] = self.shelf_selections[old_name]
      del self.shelf_selections[old_name]
    

    @logged(remove_on_chart_removal=False)
    def remove_selection_from_shelf(self, df_name: str):
      del self.shelf_selections[df_name]


    def create_custom_visualization(self, spec):
        """[summary]
        
        Arguments:
            spec {[type]} -- the spec must contain all but the data information.
        """
        return


    def custom_message(self, message_type: str, message: str):
        """[internal] escape hatch for other message types
        
        Arguments:
            type {str} -- the typescript code must know how to handle this "type"
            message {str} -- propages the "value" of the message sent
        """
        self.comm.send({
            "type": message_type,
            "value": message
        })

    def create_distribution_query(self, col_name: str, df_name: str) -> str:
        '''
        directly generating the queries out of convenience,
           since lambda expressions are used...
        '''

        df_info = self.get_df(DFName(df_name))
        if df_info is None:
            raise InternalLogicalError("Should not be getting distribution on unregistered dataframes and columns")
        df = df_info.df
        col_value = df.table.column(col_name)
        new_name = f"{col_name}_distribution"
        if (is_string_dtype(col_value)):
            code = f"{new_name} = {df.df_name}.group('{col_name}')"
            return code
        elif (is_datetime64_any_dtype(col_value)):
            # TODO temporal bining, @Ryan?
            raise NotImplementedError("Cannot bin temporal values yet")
        else:
            # we need to write the binning function and then print it out...
            # get the bound
            unique_vals = np.unique(col_value)
            current_max_bins = len(unique_vals)
            if (current_max_bins < MAX_BINS):
                code = f"{new_name} = {df.df_name}.group('{col_name}')"
                return code

            # TODO(: the distribution is a little too coarse grained
            #           with data like this: s = np.random.normal(0, 0.1, 20)

            min_bucket_count = round(current_max_bins/MAX_BINS)
            d_max = unique_vals[-1]
            d_min = unique_vals[0]
            min_bucket_size = (d_max - d_min) / min_bucket_count
            # print(MAX_BINS, current_max_bins, d_max, d_min)
            bound = snap_to_nice_number(min_bucket_size)
            bin_column_name = f"{col_name}_bin"
            binning_lambda = f"lambda x: int(x/{bound}) * {bound}"
            bin_transform = f"{df.df_name}.append_column('{bin_column_name}', {df.df_name}.apply({binning_lambda}, '{col_name}'))"
            grouping_transform = f"{new_name} = {df.df_name}.group('{bin_column_name}')"
            code = f"{bin_transform}\n{grouping_transform}"
            return code
