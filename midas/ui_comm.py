from midas.midas_algebra.data_types import NotAllCaseHandledError
from midas.state_types import DFName
from ipykernel.comm import Comm
from json import loads
from datetime import datetime
from typing import Dict, Callable, Any
import json

from .constants import MIDAS_CELL_COMM_NAME
from ast import literal_eval

from midas.midas_algebra.dataframe import MidasDataFrame
from .util.utils import get_min_max_tuple_from_list
from .util.errors import InternalLogicalError, MockComm, debug_log
from .vis_types import ChartType, NullSelectionPredicate, Channel, TwoDimSelectionPredicate, OneDimSelectionPredicate, ChartInfo
from .util.helper import transform_df, get_chart_title
from .widget.showme import gen_spec
from .util.data_processing import sanitize_dataframe

class UiComm(object):
    comm: Comm
    vis_spec: Dict[DFName, ChartInfo]
    is_in_ipynb: bool
    tmp_debug: str

    def __init__(self, is_in_ipynb: bool, add_selection: Callable[[str, str], Any]):
        self.next_id = 0
        self.vis_spec = {}
        self.is_in_ipynb = is_in_ipynb
        self.set_comm()
        self.add_selection = add_selection


    def set_comm(self):
        if self.is_in_ipynb:
            self.comm = Comm(target_name=MIDAS_CELL_COMM_NAME)

            def handle_msg(data_raw):
                self.tmp_debug = data_raw
                # data_raw = loads(data_str)
                data = data_raw["content"]["data"]
                command = data["command"]
                if (command == "selection"):
                    df_name = data["dfName"]
                    value = data["value"]
                    self.send_debug_msg(f"Data: {command} {df_name} {value}")
                    self.add_selection(df_name, value)
                else:
                    m = f"Command {command} not handled!"
                    self.send_debug_msg(m)
                    raise NotAllCaseHandledError(m)

            self.comm.on_msg(handle_msg)
        else:
            self.comm = MockComm()
    

    def visualize(self, df: MidasDataFrame):
        if (len(df.pandas_value.columns) > 2):
            self.send_user_error(f"Dataframe {df.df_name} not visualized")
        else:
            if (df.df_name in self.vis_spec):
                self.update_chart(df)
            else:
                self.create_chart(df)
        return

    def create_profile(self, df: MidasDataFrame):
        debug_log(f"creating profile {df.df_name}")
        if df.df_name is None:
            raise InternalLogicalError("df should have a name to be updated")
        # clean_df = sanitize_dataframe(df.pandas_value)
        # data = json.dumps(clean_df.to_json(orient="table"))
        columns = [{"columnName": c.name, "columnType": c.c_type.value} for c in df.columns]
        # print(columns)
        message = {
            "type": "profiler",
            "dfName": df.df_name,
            "columns": json.dumps(columns)
        }
        self.comm.send(message)
        return

    def create_chart(self, mdf: MidasDataFrame):
        if mdf.df_name is None:
            raise InternalLogicalError("df should have a name to be updated")
        
        df = mdf.pandas_value
        if (len(df.columns) > 2):
            raise InternalLogicalError("create_chart should not be called")
        chart_title = get_chart_title(mdf.df_name) # type: ignore
        chart_info = gen_spec(df, chart_title)
        if chart_info:
            # now we set the date for everyone
            vis_df = df
            if chart_info.additional_transforms:
                vis_df = transform_df(chart_info.additional_transforms, df)
            if vis_df is None:
                self.send_user_error(f"Df {mdf.df_name} is empty")
                return
            sanitizied_df = sanitize_dataframe(vis_df)
            # we have created it such that the data is an array
            chart_info.vega_spec["data"][0]["values"] = sanitizied_df.to_dict(orient='records')
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
            # return self._visualize_df_with_spec(df_name, spec, set_data=False)
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
        pandas_df = df.pandas_value
        vis_df = pandas_df
        if chart_info.additional_transforms:
            vis_df = transform_df(chart_info.additional_transforms, pandas_df)

        sanitizied_df = sanitize_dataframe(vis_df)
        # we have created it such that the data is an array
        new_data = sanitizied_df.to_dict(orient='records')

        # should be very similar to above
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

    def send_debug_msg(self, message: str):
        self.comm.send({
            "type": "notification",
            "style": "debug",
            "value": message
        })

    def navigate_to_chart(self, df_name: DFName):
        # @ryan --- I think this should be very simialr to the concurrent scrolling
        #           do you mind looking into it?
        raise NotImplementedError()

    def get_predicate_info(self, df_name: DFName, selection: str):
        interaction_time = datetime.now()
        if (len(selection) == 0):
            predicate = NullSelectionPredicate(interaction_time)
            return predicate
        predicate_raw = loads(selection)
        vis = self.vis_spec[df_name]
        x_column = vis.encodings[Channel.x]
        y_column = vis.encodings[Channel.y]
        if (vis.chart_type == ChartType.scatter):
            x_value = get_min_max_tuple_from_list(predicate_raw[Channel.x.value])
            y_value = get_min_max_tuple_from_list(predicate_raw[Channel.y.value])
            predicate = TwoDimSelectionPredicate(interaction_time, x_column, y_column, x_value, y_value)
            return predicate
        if (vis.chart_type == ChartType.bar_categorical):
            x_value = predicate_raw[Channel.x.value]
            is_categorical = True
            predicate = OneDimSelectionPredicate(interaction_time, x_column, is_categorical, x_value)
            return predicate
        if (vis.chart_type == ChartType.bar_linear):
            print("===debug===")
            print(predicate_raw[Channel.x.value])
            # bounds = []
            # left = literal_eval((predicate_raw[Channel.x.value][0].replace('(','[')))
            # bounds.append(left[0])
            # right = literal_eval((predicate_raw[Channel.x.value][-1].replace('(','[')))
            # bounds.append(right[1]
            # x_value = get_min_max_tuple_from_list([bound_left, bound_right])
            x_value = get_min_max_tuple_from_list(predicate_raw[Channel.x.value])
            is_categorical = False
            predicate = OneDimSelectionPredicate(interaction_time, x_column, is_categorical, x_value)
            return predicate
        if (vis.chart_type == ChartType.line):
            x_value = get_min_max_tuple_from_list(predicate_raw[Channel.x.value])
            is_categorical = False
            predicate = OneDimSelectionPredicate(interaction_time, x_column, is_categorical, x_value)
            return predicate
        # now 
        raise InternalLogicalError("Not all chart_info handled")




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

   