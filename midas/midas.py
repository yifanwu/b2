from __future__ import absolute_import
from pandas import DataFrame, read_csv, read_json
from typing import Dict, Optional, List, Callable, Union, cast
from datetime import datetime, timedelta
from json import loads
import ipywidgets

try:
    from IPython.display import display
except ImportError as err:
    print("not in Notebook environment")
    display = lambda x: None
    logging = lambda x, y: None

from .config import THROTTLE_RATE_MS
from .errors import NullValueError, DfNotFoundError, InternalLogicalError, UserError, \
    report_error_to_user, logging, debug_log, report_error_to_user, \
    check_not_null
from .utils import get_min_max_tuple_from_list
from .helper import get_df_by_predicate
from .showme import gen_spec, set_data_attr
from .vega_gen.defaults import SELECTION_SIGNAL
from .widget import MidasWidget
from .vega_gen.data_processing import get_categorical_distribution, get_numeric_distribution
from .types import DFInfo, ChartType, ChartInfo, TickSpec, DfTransform, \
    TwoDimSelectionPredicate, OneDimSelectionPredicate, \
    SelectionPredicate, Channel, DFDerivation, DerivationType, \
    DFLoc, TickItem, JoinInfo, Visualization, \
    PredicateCallback, TickCallbackType, DataFrameCall, PredicateCall
    

CUSTOM_FUNC_PREFIX = "__m_"
MIDAS_INSTANCE_NAME = "m"

class Midas(object):
    """[summary]
    
    functions prefixed with "js_" is invoked by the js layer.
    """
    dfs: Dict[str, DFInfo]
    tick_funcs: Dict[str, List[TickItem]]
    joins: List[JoinInfo]

    def __init__(self, m_name=MIDAS_INSTANCE_NAME):
        self.dfs = {}
        self.tick_funcs = {}
        self.m_name: str = m_name
        self.current_tick: int = 0
        self.is_processing_tick: bool = False
        self.tick_queue: List[TickSpec] = []
        # TODO: maybe we can just change the DataFrame here...
        # self._pandas_magic()

    def loc(self, df_name: str, new_df_name: str, rows: Optional[Union[slice, List[int]]] = None, columns: Optional[Union[slice, List[str]]] = None) -> DataFrame:
        """this is a wrapper around the DataFrame `loc` function so that Midas will
        help keep track
        
        Arguments:
            df_name {str} -- [description]
            new_df_name {str} -- [description]
            columns {slice} -- [description]
            rows {slice} -- [description]
        
        Returns:
            DataFrame -- the new dataframe that's is returned 
        """
        # need to pass in, named, df, rows, columns, and the new name of the df
        found = self.dfs[df_name]
        filled_rows = rows if rows else slice(None, None, None)
        filled_columns = columns if columns else slice(None, None, None)
        new_df = found.df.loc[filled_rows, filled_columns]
        loc_spec = DFLoc(filled_rows, filled_columns)
        self.register_df(new_df, new_df_name, DFDerivation(df_name, new_df_name, DerivationType.loc, loc_spec))
        return new_df


    def get_df(self, df_name: str):
        # all the dfs are named via the global var so we can manipulate without worrying about reference changes!
        if (df_name in self.dfs):
            return self.dfs[df_name].df
        else:
            return None


    def register_df(self, df: DataFrame, df_name: str, derivation=None):
        """pivate method to keep track of dfs
            TODO: make the meta_data work with the objects
        """
        logging("register_df", df_name)
        created_on = datetime.now()
        selections: List[SelectionPredicate] = []
        chart_spec = None # to be populated later
        df_info = DFInfo(df_name, df, created_on, selections, derivation, chart_spec)
        self.dfs[df_name] = df_info
        self.__show_or_rename_visualization(df_name)
        return


    def remove_df(self, df_name: str):
        self.dfs.pop(df_name)


    def __show_or_rename_visualization(self, df_name: str):
        return self.visualize_df_without_spec(df_name)


    def read_json(self, path: str, df_name: str, **kwargs):
        df = read_json(path, kwargs)
        self.register_df(df, df_name)
        return df


    def read_csv(self, path: str, df_name: str, **kwargs):
        df = read_csv(path, kwargs)
        # meta_data = DfMetaData(time_created = datetime.now())
        self.register_df(df, df_name)
        return df


    def get_df_to_visualize_from_context(self):
        # if (df_name == None):
        #     df = self.get_df_to_visualize_from_context()
        # el
        
        raise NotImplementedError()


    # note that spec is defaulted to none without the Optional signature because there is no typing for JSON.
    def visualize_df(self, df_name: str, spec: Optional[ChartInfo]=None):
        # generate default spec
        if spec:
            return self.visualize_df_with_spec(df_name, spec, set_data = True)
        else:
            # see if it's stored
            vis = self.dfs[df_name].visualization
            if vis:
                stored_info = vis.chart_info
            else:
                raise NullValueError('visualization should be set by now')
            if (stored_info != None):
                return self.visualize_df_with_spec(df_name, stored_info, set_data = True)
            return self.visualize_df_without_spec(df_name)


    def visualize_df_without_spec(self, df_name: str):
        df = self.get_df(df_name)
        spec = gen_spec(df)
        if spec:
            # set_data is false because gen_spec already sets the data
            return self.visualize_df_with_spec(df_name, spec, set_data=False)
        else:
            # TODO: add better explanations
            report_error_to_user("we could not generat the spec")


    def _tick(self, df_name: str, history_index: int):
        if self.is_processing_tick:
            # see if we need to throttle
            # check the last item on the queue
            if (len(self.tick_queue) > 0):
                if (self.tick_queue[-1].start_time > datetime.now() - timedelta(milliseconds = THROTTLE_RATE_MS)):
                    # don't even add to tick
                    logging("throttled", df_name)
                    return
            
            # put on queue and return
            logging("tick", f"queuing {df_name} at {history_index}")
            self.tick_queue.append(TickSpec(df_name, history_index, datetime.now()))
            return

        logging("tick", f"processing {df_name} with history {history_index}")
        self.is_processing_tick = True
        print("actually processing")
        self._process_tick(df_name, history_index)
        self.is_processing_tick = False


    def _process_tick(self, df_name: str, history_index: int):
        self.current_tick += 1
        # see if we need to wait
        # checkthe tick item
        predicate, df_info = self._get_selection_by_predicate(df_name, history_index)
        if not predicate:
            return
        lineage_data: DataFrame = None
        items = self.tick_funcs.get(df_name)
        logging("tick", f"for predicate{predicate}")
        if items:
            for _, i in enumerate(items):
                logging("  callback", f"{i}")
                if (i.callback_type == TickCallbackType.predicate):
                    i.call.func(predicate)
                else:
                    _call = cast(DataFrameCall, i.call)
                    if lineage_data is None:
                        lineage_data = get_df_by_predicate(df_info.df, predicate)
                    new_data = _call.func(lineage_data)
                    
                    # only update if this is not null
                    if new_data is not None:
                        if (len(new_data.index) > 0):
                            # register data if this is the first time that this is called
                            if not self._has_df(_call.target_df):
                                self.register_df(new_data, _call.target_df)
                            else:
                                # see if we need to do any transforms..
                                vis_data = new_data
                                # we need to look up the target...
                                df_target_additional_transforms = self.dfs[_call.target_df].visualization.chart_info.additional_transforms
                                if (df_target_additional_transforms == DfTransform.categorical_distribution):
                                    first_col = new_data.columns.values[0]
                                    vis_data = get_categorical_distribution(new_data[first_col], first_col)
                                elif (df_target_additional_transforms == DfTransform.numeric_distribution):
                                    first_col = new_data.columns.values[0]
                                    vis_data = get_numeric_distribution(new_data[first_col], first_col)

                                # update the data in store
                                self.set_df_data(_call.target_df, new_data)
                                # send the update
                                vis = self.dfs[_call.target_df].visualization
                                if vis:
                                    vis.widget.replace_data(vis_data)
                        else:
                            report_error_to_user(f"Transformation result on {df_name} was empty")
                    else:
                        raise UserError("Transformation result was not defined")

        
        # if queue is not empty, invoke it
        if (len(self.tick_queue) > 0):
            # push the first one off, FIFO
            to_process = self.tick_queue.pop(0)
            self._process_tick(to_process.df_name, to_process.history_index)
        return


    def set_df_data(self, df_name: str, df: DataFrame):
        if self._has_df(df_name):
            self.dfs[df_name] = self.dfs[df_name]._replace(df = df)
        else:
            raise InternalLogicalError("df not defined")


    def js_add_selection(self, df_name: str, selection: str):
        logging("js_add_selection", df_name)
        # figure out what spec it was
        df_info = self.dfs[df_name]
        check_not_null(df_info)
        predicate_raw = loads(selection)
        interaction_time = datetime.now()
        vis = df_info.visualization
        predicate: SelectionPredicate
        c_type = df_info.visualization.chart_info.chart_type
        # the following two, x_column, y_column are shared by all chart types
        x_column = vis.chart_info.encodings[Channel.x]
        y_column = vis.chart_info.encodings[Channel.y]
        if vis:
            if (c_type == ChartType.scatter):
                x_value = get_min_max_tuple_from_list(predicate_raw[Channel.x.value])
                y_value = get_min_max_tuple_from_list(predicate_raw[Channel.y.value])
                predicate = TwoDimSelectionPredicate(interaction_time, x_column, y_column, x_value, y_value)
            elif (c_type == ChartType.bar_categorical):
                x_value = predicate_raw[Channel.x.value]
                is_categorical = True
                predicate = OneDimSelectionPredicate(interaction_time, x_column, is_categorical, x_value)
            elif (c_type == ChartType.bar_linear):
                bound_left = predicate_raw[Channel.x.value][0][0]
                bound_right = predicate_raw[Channel.x.value][-1][1]
                x_value = get_min_max_tuple_from_list([bound_left, bound_right])
                is_categorical = False
                predicate = OneDimSelectionPredicate(interaction_time, x_column, is_categorical, x_value)
            else:
                x_value = get_min_max_tuple_from_list(predicate_raw[Channel.x.value])
                is_categorical = False
                predicate = OneDimSelectionPredicate(interaction_time, x_column, is_categorical, x_value)

            history_index = len(df_info.predicates)
            df_info.predicates.append(predicate)
            self._tick(df_name, history_index)
        return
        

    def _get_selection_by_predicate(self, df_name: str, history_index: int):
        df_info = self.dfs[df_name]
        check_not_null(df_info)
        if (len(df_info.predicates) > history_index):
            predicate = df_info.predicates[history_index]
            return predicate, df_info
        else:
            raise DfNotFoundError(df_name)


    def get_current_selection(self, df_name: str, option: str="predicate"):
        """[summary]
        
        Arguments:
            df_name {str} -- [description]
            option {str} -- two options, "predicate" or "data", defaults to "predicate"
        
        Returns:
            [type] -- [description]
        """
        df_info = self.dfs[df_name]
        check_not_null(df_info)
        if (len(df_info.predicates) > 0):
            predicate = df_info.predicates[-1]
            if (option == "predicate"):
                return predicate
            else:
                return get_df_by_predicate(df_info.df, predicate)
        else:
            return None



    def get_selection_history(self, df_name: str):
        found = self.dfs[df_name]
        if (found != None):
            return found.predicates
        else:
            return None 


    def _add_to_tick(self, df_name: str, item: TickItem):
        logging("_add_to_tick", f" called{df_name}\n{item}")
        if (df_name in self.tick_funcs):
            self.tick_funcs[df_name].append(item)
        else:
            self.tick_funcs[df_name] = [item]


    def add_callback_to_selection(self,
        df_name: str,
        cb: PredicateCallback
      ):
        # first make sure that the df is in
        if not (self._has_df(df_name)):

            raise DfNotFoundError(f"{df_name} is not in the collection of {self.dfs.keys()}")
        # we'll put this inside the python so it's not all generated by the janky JS
        call = PredicateCall(cb)
        item = TickItem(TickCallbackType.predicate, call)
        self._add_to_tick(df_name, item)

        return

    def _has_df(self, df_name: str):
        if (df_name in self.dfs):
            return True
        else:
            return False
        
    
    def new_visualization_from_selection(self, df_interact_name: str, new_df_name: str, df_transformation: Callable[[DataFrame], DataFrame]):
        """
        This is used for blackbox style visualizations
    
        Arguments:
            df_interact_name {str} -- specify the interaction whose selection will be used as the basis
            new_df_name {str} -- [description]
            df_transformation {Callable[[DataFrame], DataFrame]} -- [description]
        
        Raises:
            NotImplementedError: [description]
        """
        if (df_interact_name not in self.dfs):
            raise UserError(f"Your interaction based df {df_interact_name} does not exists")
        if (new_df_name in self.dfs):
            raise UserError(f"Your result based df {df_interact_name} does not exists")

        call = DataFrameCall(df_transformation, new_df_name)
        item = TickItem(TickCallbackType.dataframe, call)
        self._add_to_tick(df_interact_name, item)
        
        # also see if the selection has already been made, if it has
        df_info = self.dfs[df_interact_name]
        if (len(df_info.predicates) > 0):
            # register it
            new_data = df_transformation(get_df_by_predicate(df_info.df, df_info.predicates[-1]))
            self.register_df(new_data, new_df_name)
        return


    def register_join_info(self, dfs: List[str], join_columns: List[str]):
        join_info = JoinInfo(dfs, join_columns)
        self.joins.append(join_info)


    def addFacet(self, df_name: str, facet_column: str):
        # 
        raise NotImplementedError()


    def link_dfs(self, df_interact_name: str, new_df_name: str):
        # infer how  df_interact_name and df_filter_name are connected to each other
        # the simplest case is that they are both columns from a large existing table
        # basically re-write the otherone if we know how to
        # then do similar as new_visualization_from_selection
        # use the predicate to link them together

        # case 1: two dfs derived from the same original df, both using loc
        #         then we can either create a new Vega spec with data, using loc
        #         or we can just go through the predicate construction via the df logic?
        #         #TODO: ask Arvind?
        raise NotImplementedError()


    # spec: VegaSpecType, encodings: Dict[Channel, str], chart_type: ChartType
    def visualize_df_with_spec(self, df_name: str, chart_info: ChartInfo, set_data=False):
        if (set_data):
            df = self.get_df(df_name)
            # note that we need to assign to a new variable, otherwise it will not load
            set_data_attr(chart_info.vega_spec, df)
        # register the spec to the df
        w = MidasWidget(chart_info.vega_spec)
        # items[node.ind] = items[node.ind]._replace(v=node.v)
        vis = Visualization(chart_info, w)
        self.dfs[df_name] = self.dfs[df_name]._replace(visualization = vis)
        # note that we use a custom prefix to avoid accidentally overwrriting a user defined function
        cb = f"""
            var {CUSTOM_FUNC_PREFIX}val_str = JSON.stringify(value);
            var pythonCommand = `{self.m_name}.js_add_selection("{df_name}", '${{{CUSTOM_FUNC_PREFIX}val_str}}')`;
            console.log("calling", pythonCommand);
            IPython.notebook.kernel.execute(pythonCommand)
        """
        w.register_signal_callback(SELECTION_SIGNAL, cb)
        out = ipywidgets.Output(layout={'border': '1px solid black'})

        with out:
          display(w)

        return w

__all__ = ['Midas']
