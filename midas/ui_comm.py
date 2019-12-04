from datetime import datetime
from midas.midas_algebra.data_types import DFId
from IPython import get_ipython 
from pandas.api.types import is_string_dtype, is_numeric_dtype, is_datetime64_any_dtype 
from midas.midas_algebra.selection import SelectionValue
from ipykernel.comm import Comm # type: ignore
import numpy as np
# from json import loads
from typing import Dict, Callable, Optional, List, cast, Tuple, Any
import json
from pyperclip import copy
import ast

from .constants import MIDAS_CELL_COMM_NAME, MAX_BINS
from midas.state_types import DFName

from midas.midas_algebra.dataframe import MidasDataFrame, RelationalOp, VisualizedDFInfo, DFInfo
from midas.midas_algebra.selection import NumericRangeSelection, SetSelection, ColumnRef
from .util.errors import InternalLogicalError, MockComm, debug_log, NotAllCaseHandledError
from .vis_types import EncodingSpec, FilterLabelOptions
from .util.data_processing import dataframe_to_dict, snap_to_nice_number
from midas.showme import infer_encoding

class UiComm(object):
    comm: Comm
    vis_spec: Dict[DFName, EncodingSpec]
    id_by_df_name: Dict[DFName, DFId]
    is_in_ipynb: bool
    midas_instance_name: str
    create_df_from_ops:  Callable[[RelationalOp], MidasDataFrame]

    def __init__(self, is_in_ipynb: bool, midas_instance_name: str,
      get_df_fun: Callable[[DFName], Optional[DFInfo]],
      create_df_from_ops: Callable[[RelationalOp], MidasDataFrame],
      add_selection: Callable[[List[SelectionValue]], List[SelectionValue]]):
        self.next_id = 0
        self.vis_spec = {}
        self.id_by_df_name = {}
        self.shelf_selections = {}
        self.is_in_ipynb = is_in_ipynb
        self.midas_instance_name = midas_instance_name
        self.set_comm(midas_instance_name)
        self.get_df = get_df_fun
        self.create_df_from_ops = create_df_from_ops
        self.add_selection = add_selection
        self.tmp_log = []

    def handle_msg(self, data_raw):
        data = data_raw["content"]["data"]
        self.tmp_log.append(data)
        debug_log(f"got message {data}")
        if "command" in data:
            command = data["command"]
            if command == "refresh-comm":
                self.send_debug_msg("Refreshing comm")
                self.set_comm(self.midas_instance_name)
                return
            if command == "cell-ran":
                if "code" in data:
                    code = data["code"]
                    self.process_code(code)
                return
            if command == "get_code_clipboard":
                df_name = DFName(data["df_name"])
                df = self.get_df(df_name)
                if df:
                    # TODO: get predicates working again
                    code = df.df.get_code()
                    copy(code)
                    return code
                # something went wrong, so let's tell comes...
                self.send_user_error(f'no selection on {df_name} yet')
            
            if command == "column-selected":
                # self.send_debug_msg("column-selected called")
                column = data["column"]
                df_name = DFName(data["df_name"])
                self.tmp = f"{column}_{df_name}"
                code = self.create_distribution_query(column, df_name)
                self.create_cell_with_text(code)
                # now we need to figure out what kind of transformation is needed
                # if nothing, we just show the table
            if command == "add_current_selection":
                value = data["value"]
                # parse it first!
                self.send_debug_msg(f"got add_current_selection message {value}")
                selections = self.get_predicate_info(value)
                all_predicate = self.add_selection(selections)
                # now turn this into JSON
                predicates = ",".join(list(map(lambda v: v.to_str(), all_predicate)))
                code = f"{self.midas_instance_name}.make_selections([{predicates}])"
                self.send_debug_msg(f"creating code\n{code}")
                self.create_cell_with_text(code)
            else:
                m = f"Command {command} not handled!"
                # self.send_debug_msg(m)
                raise NotAllCaseHandledError(m)
        else:
            debug_log(f"Got message from JS Comm: {data}")

    def process_code(self, code: str):
        assigned_dfs = self.get_dfs_from_code_str(code)
        # assigned_dfs_str = ",".join([cast(str, df.df_name) for df in assigned_dfs])
        # we need to create the code
        if len(assigned_dfs) == 0:
            # do nothing
            debug_log("no df to process")
            return
        code_lines = []
        for df in assigned_dfs:
            if df.is_base_df:
                line = f"{df.df_name}.show_profile()"
            else:
                encoding = infer_encoding(df)
                encoding_arg = f"shape='{encoding.shape}', x='{encoding.x}', y='{encoding.y}'"
                line = f"{df.df_name}.show({encoding_arg})"
            code_lines.append(line)
        code = "\n".join(code_lines)
        self.create_cell_with_text(code)

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


    def create_chart(self, mdf: MidasDataFrame, encoding: EncodingSpec):
        # debug_log(f"creating chart {mdf.df_name}")
        if mdf.df_name is None:
            raise InternalLogicalError("df should have a name to be updated")
        # first check if the encodings has changed
        if mdf.df_name in self.vis_spec:
            if self.vis_spec[mdf.df_name] == encoding and self.id_by_df_name[mdf.df_name] == mdf.id:
                # no op
                debug_log("no op, same stuff")
                return

        self.vis_spec[mdf.df_name] = encoding
        self.id_by_df_name[mdf.df_name] = mdf.id

        # vega_lite = gen_spec(mdf.df_name, encoding)
        records = dataframe_to_dict(mdf, FilterLabelOptions.unfiltered)
        # TODO: check if we even need to do the dumping
        data = json.dumps(records)
        message = {
            'type': 'chart_render',
            "dfName": mdf.df_name,
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
    

    def update_chart_filtered_value(self, df: Optional[MidasDataFrame], df_name: DFName):
        # note that this is alwsays used for updating filtered information
        if df_name not in self.vis_spec:
            raise InternalLogicalError("Cannot update since not done before")
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
        
    def create_cell_with_text(self, s):
        # self.send_debug_msg(f"create_cell_with_text called {s}")
        d = datetime.now().replace(microsecond=0)
        annotated = f"# [MIDAS] auto-created on {d}\n{s}"
        self.send_debug_msg(f"creating cell: {annotated}")
        self.comm.send({
            "type": "create_then_execute_cell",
            "value": annotated
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
        

    def get_predicate_info(self, selections: Dict) -> List[SelectionValue]:
        # debug_log(f"selection is {selection}")
        if selections is None or len(selections.keys()) == 0:
            return []
        result = []
        for df_name in selections:
            selection = selections[df_name]
            vis = self.vis_spec[df_name]
            if vis.shape == "circle":
                x_selection = NumericRangeSelection(ColumnRef(vis.x, df_name), selection[vis.x][0], selection[vis.x][1])
                y_selection = NumericRangeSelection(ColumnRef(vis.y, df_name), selection[vis.y][0], selection[vis.y][1])
                result.extend([x_selection, y_selection])
            elif vis.shape == "bar":
                predicate = SetSelection(ColumnRef(vis.x, df_name), selection[vis.x])
                result.extend([predicate])
            elif vis.shape == "line":
                x_selection = NumericRangeSelection(ColumnRef(vis.x, df_name), selection[vis.x][0], selection[vis.x][1])
                result.extend([x_selection])
            else:
                raise InternalLogicalError(f"{vis.shape} not handled")
        return result

    def update_selection_shelf_selection_name(self, old_name: str, new_name: str):
      self.shelf_selections[new_name] = self.shelf_selections[old_name]
      del self.shelf_selections[old_name]
    

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
