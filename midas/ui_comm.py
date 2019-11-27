from datetime import datetime
from midas.midas_algebra.selection import SelectionValue
from ipykernel.comm import Comm # type: ignore
from json import loads
from typing import Dict, Callable, Any, List, cast
import json
from pyperclip import copy

from .constants import MIDAS_CELL_COMM_NAME
from midas.state_types import DFName

from midas.midas_algebra.dataframe import MidasDataFrame, VisualizedDFInfo
from midas.midas_algebra.selection import NumericRangeSelection, StringSetSelection, SingleValueSelection, ColumnRef
from .util.utils import get_min_max_tuple_from_list
from .util.errors import InternalLogicalError, MockComm, debug_log, NotAllCaseHandledError
from .vis_types import ChartType, Channel, ChartInfo, SelectionEvent
from .util.data_processing import dataframe_to_dict, transform_df

class Updated():
    MidasDataFrame

class UiComm(object):
    comm: Comm
    vis_spec: Dict[DFName, ChartInfo]
    is_in_ipynb: bool
    tmp_debug: str
    midas_instance_name: str
    

    def __init__(self, is_in_ipynb: bool, midas_instance_name: str, get_df_fun):
        self.next_id = 0
        self.vis_spec = {}
        self.shelf_selections = {}
        self.is_in_ipynb = is_in_ipynb
        self.set_comm(midas_instance_name)
        self.get_df = get_df_fun
        

    def set_comm(self, midas_instance_name: str):
        if self.is_in_ipynb:
            self.comm = Comm(target_name = MIDAS_CELL_COMM_NAME)
            # tell the JS side what the assigned name is
            self.comm.send({
                "type": "midas_instance_name",
                "value": midas_instance_name
            })

            def handle_msg(data_raw):
                self.tmp_debug = data_raw
                # data_raw = loads(data_str)
                data = data_raw["content"]["data"]
                if "command" in data:
                    command = data["command"]
                    if command == "refresh-comm":
                        self.send_debug_msg("Refreshing comm")
                        self.set_comm(midas_instance_name)
                        return
                    if command == "cell-ran":
                        if "code" in data:
                            code = data["code"]
                            # TODO: some information we can analyze later...
                            # analyze the code that was ran
                            # if it was a mdias_df
                            # self.actual_visualize()
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
                    if command == "add_selection":
                        df_name = DFName(data["df_name"])
                        df_info = cast(VisualizedDFInfo, self.get_df(df_name))
                        predicates = df_info.predicates
                        if (len(predicates) > 0):
                            predicate = predicates[-1]
                            name = f"{predicate.df_name}_{len(predicates)}"

                            self.shelf_selections[name] = (predicate, df_name)
                            self.custom_message('add-selection', name)
                        else: 
                            self.send_user_error(f'no selection on {df_name} yet')
                        # then need to trigger the method on midas...
                    # if (command == "selection"):
                    #     df_name = data["dfName"]
                    #     value = data["value"]
                    #     self.send_debug_msg(f"Data: {command} {df_name} {value}")
                    #     # now we need to process the value
                    #     predicate = self.get_predicate_info(df_name, value)
                    #     date = datetime.now()
                    #     selection_event = SelectionEvent(date, predicate, DFName(df_name))
                    #     self.ui_add_selection(selection_event)
                    else:
                        m = f"Command {command} not handled!"
                        self.send_debug_msg(m)
                        raise NotAllCaseHandledError(m)
                else:
                    debug_log(f"Got message from JS Comm: {data}")

            self.comm.on_msg(handle_msg)
        else:
            self.comm = MockComm()
    
    # should be idempotent in case the code analysis has false positives
    # def actual_visualize(self, df_name: str):
    #     df = self.current_df_chain[DFName(df_name)]

    def visualize(self, df: MidasDataFrame, is_original: bool=True):
        # if it is filter based, then we update_chart, otherweise, we need to REPLACE the chart
        # let's put this on a stack and only keep the most recent one
        # the visualize is actually trigger
        if df.df_name is None:
            raise InternalLogicalError("df_name should be defined already")
        
        if df is None:
            raise InternalLogicalError("df should be defined already")
        if (len(df.table.columns) > 2):
            self.send_user_error(f"Dataframe {df.df_name} not visualized")
            return False
        else:
            if (df.df_name in self.vis_spec):
                self.update_chart(df)
            else:
                self.create_chart(df)
            return True

    def create_profile(self, df: MidasDataFrame):
        debug_log(f"creating profile {df.df_name}")
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

    def create_chart(self, mdf: MidasDataFrame):
        debug_log(f"creating chart {mdf.df_name}")
        if mdf.df_name is None:
            raise InternalLogicalError("df should have a name to be updated")
        
        df = mdf.table
        if (len(df.columns) > 2):
            raise InternalLogicalError("create_chart should not be called")
        chart_title = mdf.df_name
        chart_info = gen_spec(df, chart_title, mdf.chart_config)
        if chart_info:
            vis_df = df
            if chart_info.additional_transforms:
                vis_df = transform_df(chart_info.additional_transforms, df)
            if vis_df is None:
                self.send_user_error(f"Df {mdf.df_name} is empty")
                return
            records = dataframe_to_dict(vis_df)
            # we have created it such that the data is an array
            # base
            chart_info.vega_spec["data"][0]["values"] = records
            # filtered --- set to be the same
            # set the spec
            self.vis_spec[mdf.df_name] = chart_info # type: ignore
            # see if we need to apply any transforms
            # note that visualizations must have 2 columns or less right now.
            vega = json.dumps(chart_info.vega_spec)
            message = {
                'type': 'chart_render',
                "dfName": mdf.df_name,
                'vega': vega
            }
            self.comm.send(message)
        else:
            # TODO: add better explanations
            self.comm.send({
                "type": "error",
                "value": "We could not generate the spec"
            })
        return


    def update_chart(self, df: MidasDataFrame):
        # first look up chart_info
        if df.df_name is None:
            raise InternalLogicalError("Missing df_name")
        chart_info = self.vis_spec[df.df_name]
        if chart_info is None:
            raise InternalLogicalError("Cannot update since not done before")
        table = df.table
        vis_df = table
        if chart_info.additional_transforms:
            vis_df = transform_df(chart_info.additional_transforms, table)

        new_data = dataframe_to_dict(vis_df)
        print("new data")
        print(new_data)
        self.comm.send({
            "type": "chart_update_data",
            "dfName": df.df_name,
            "newData": new_data
        })
        return

    def send_user_error(self, message: str):
        self.comm.send({
            "type": "notification",
            "style": "error",
            "value": message
        })

    def execute_current_cell(self):
        self.comm.send({
            "type": "execute_current_cell"
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
        

    def get_predicate_info(self, df_name: DFName, selection) -> List[SelectionValue]:
        debug_log(f"selection is {selection}")
        if selection is None:
            return []
        # loads
        predicate_raw = selection
        vis = self.vis_spec[df_name]
        x_column = vis.encodings[Channel.x]
        y_column = vis.encodings[Channel.y]
        if vis.chart_type == ChartType.scatter:
            x_value = get_min_max_tuple_from_list(predicate_raw[Channel.x.value])
            y_value = get_min_max_tuple_from_list(predicate_raw[Channel.y.value])
            x_selection = NumericRangeSelection(ColumnRef(x_column, df_name), x_value[0], x_value[1])
            y_selection = NumericRangeSelection(ColumnRef(y_column, df_name), y_value[0], y_value[1])
            return [x_selection, y_selection]
        if vis.chart_type == ChartType.bar_categorical:
            x_value = predicate_raw[Channel.x.value]
            predicate = StringSetSelection(ColumnRef(x_column, df_name), x_value)
            return [predicate]
        if vis.chart_type == ChartType.bar_linear:
            x_value = get_min_max_tuple_from_list(predicate_raw[Channel.x.value])
            x_selection = NumericRangeSelection(ColumnRef(x_column, df_name), x_value[0], x_value[1])
            return [x_selection]
        if vis.chart_type == ChartType.line:
            x_value = get_min_max_tuple_from_list(predicate_raw[Channel.x.value])
            x_selection = NumericRangeSelection(ColumnRef(x_column, df_name), x_value[0], x_value[1])
            return [x_selection]
        raise InternalLogicalError("Not all chart_info handled")


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


    def get_chart_type(self, df_name: DFName):
        info = self.vis_spec[df_name]
        if info:
            return info.chart_type
        return None

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

   