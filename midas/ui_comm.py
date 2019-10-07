from midas.state_types import DFName
from ipykernel.comm import Comm
from json import loads
from datetime import datetime
from typing import Dict
import json

from .constants import MIDAS_CELL_COMM_NAME

from midas.midas_algebra.dataframe import MidasDataFrame
from .util.utils import get_min_max_tuple_from_list
from .util.errors import InternalLogicalError, MockComm
from .vis_types import ChartType, NullSelectionPredicate, Channel, TwoDimSelectionPredicate, OneDimSelectionPredicate, ChartInfo
from .util.helper import transform_df, get_chart_title
from .widget.showme import gen_spec
from .util.data_processing import sanitize_dataframe


class UiComm(object):
    comm: Comm
    vis_spec: Dict[DFName, ChartInfo]

    def __init__(self, is_in_ipynb: bool):
        self.next_id = 0
        self.vis_spec = {}
        if is_in_ipynb:
            self.comm = Comm(target_name=MIDAS_CELL_COMM_NAME)
        else:
            self.comm = MockComm()

    def visualize(self, df_name: DFName, df: MidasDataFrame):
        # if it's more than two we give profile
        # and less than two we plot
        # potentially add metadata here
        # make sure that value is defined

        if(df.id in self.vis_spec):
            # might be changes that require updates
            # TODO
            # direct to the right visualization
            self.comm.send({
                "type": "navigate_to_vis",
                "value": df.name
            })
            return
        if (len(df.value.columns) > 2):
            self.create_profile(df_name, df)
        else:
            self.create_chart(df_name, df)
        return

    
    def create_profile(self,  df_name: DFName, df: MidasDataFrame):
        data = json.dumps(df.value.to_json(orient="table"))
        message = {
            "type": "profiler",
            "dfName": df.name,
            "data": data
        }
        self.comm.send(message)
        return

    def create_chart(self, df_name: DFName, mdf: MidasDataFrame):
        df = mdf.value
        if (len(df.columns) > 2):
            raise InternalLogicalError("create_chart should not be called")
        chart_title = get_chart_title(df_name)
        chart_info = gen_spec(df, chart_title)
        if chart_info:
            # now we set the date for everyone
            vis_df = df
            if chart_info.additional_transforms:
                vis_df = transform_df(chart_info.additional_transforms, df)

            sanitzied_df = sanitize_dataframe(vis_df)
            # we have created it such that the data is an array
            chart_info.vega_spec["data"][0]["values"] = sanitzied_df.to_dict(orient='records')
            # set the spec
            self.vis_spec[df_name] = chart_info
            # see if we need to apply any transforms
            # note that visualizations must have 2 columns or less right now.
            vega = json.dumps(chart_info.vega_spec)
            mesage = {
                'type': 'chart_render',
                "dfName": df_name,
                'vega': vega
            }
            self.comm.send(mesage)
            # return self._visualize_df_with_spec(df_name, spec, set_data=False)
        else:
            # TODO: add better explanations
            self.comm.send({
                "type": "error",
                "value": "We could not generat the spec"
            })
        return


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
            bound_left = predicate_raw[Channel.x.value][0][0]
            bound_right = predicate_raw[Channel.x.value][-1][1]
            x_value = get_min_max_tuple_from_list([bound_left, bound_right])
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



    def update_chart(self, df_name: str, df: MidasDataFrame):
        # should be very similar to above
        return


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