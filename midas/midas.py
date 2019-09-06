from __future__ import absolute_import
from pandas import DataFrame, Series, read_csv, read_json
from typing import Dict, Optional, List, Callable, Union, cast
from datetime import datetime, timedelta
from json import loads
import ipywidgets
from IPython import get_ipython
from pyperclip import copy
from ipykernel.comm import Comm

try:
    from IPython.display import display
except ImportError as err:
    print("not in Notebook environment")
    display = lambda x: None
    logging = lambda x, y: None

# from .config import DEBOUNCE_RATE_MS
from .midas_magic import MidasMagic
from .instructions import HELP_INSTRUCTION
from .errors import NullValueError, DfNotFoundError, InternalLogicalError, UserError, \
    report_error_to_user, logging, debug_log, report_error_to_user, \
    check_not_null
from .utils import get_min_max_tuple_from_list, check_path, get_random_string, in_ipynb
from .helper import get_df_by_predicate, get_df_transform_func_by_index, get_chart_title, get_df_code, get_selection_by_predicate
from .showme import gen_spec, set_data_attr
from .vega_gen.defaults import SELECTION_SIGNAL
from .widget import MidasWidget
from .constants import CUSTOM_INDEX_NAME, MIDAS_CELL_COMM_NAME
from .vega_gen.data_processing import get_categorical_distribution, get_numeric_distribution
from .types import DFInfo, ChartType, ChartInfo, TickSpec, DfTransform, \
    TwoDimSelectionPredicate, OneDimSelectionPredicate, NullSelectionPredicate, \
    SelectionPredicate, Channel, DFDerivation, DerivationType, \
    DFLoc, TickItem, JoinInfo, Visualization, \
    PredicateCallback, DataFrameCallback, PredicateToDataFrameCallback, DataFrameToDataFrameCallback, \
    TickIOType    

CUSTOM_FUNC_PREFIX = "__m_"
MIDAS_INSTANCE_NAME = "m"

class Midas(object):
    """[summary]
    
    functions prefixed with "js_" is invoked by the js layer.
    """
    dfs: Dict[str, DFInfo]
    tick_funcs: Dict[str, List[TickItem]]
    joins: List[JoinInfo]
    nextId: int
    midas_cell_comm: Comm
    is_in_ipynb: bool

    def __init__(self):
        self.nextId = 0
        self.dfs = {}
        self.tick_funcs = {}
        self.current_tick: int = 0
        
        try:
            get_ipython()
            self.is_in_ipynb = True
        except:
            print("not in notebooks")
            self.is_in_ipynb = False

        # self.is_processing_tick: bool = False
        self.tick_log: List[TickSpec] = []
        self.midas_cell_comm = None
        # check if we are in a ipython environment
        if self.is_in_ipynb:
            midas_cell_comm = Comm(target_name=MIDAS_CELL_COMM_NAME)
            self.midas_cell_comm = midas_cell_comm
            ip = get_ipython()
            magics = MidasMagic(ip, midas_cell_comm)
            ip.register_magics(magics)
    
    def _next_id(self):
      to_return = self.nextId
      self.nextId += 1
      return to_return
        
    # -------------------------------------------------------------------------------
    # DEFINITELY INTERNAL

    def _has_df(self, df_name: str):
        if (df_name in self.dfs):
            return True
        else:
            return False


    def _get_id(self, df_name: str):
        if self._has_df(df_name):
          return self.dfs[df_name].df_id
        else:
          return self._next_id()


    def _add_to_tick(self, df_name: str, item: TickItem):
        logging("_add_to_tick", f" called{df_name}\n{item}")
        if (df_name in self.tick_funcs):
            self.tick_funcs[df_name].append(item)
        else:
            self.tick_funcs[df_name] = [item]

    def __show_or_rename_visualization(self, df_name: str):
        return self.visualize_df_without_spec(df_name)
    
    # -------------------------------------------------------------------------------
    # MOSTLY INTERNAL

    def get_df(self, df_name: str):
        # all the dfs are named via the global var so we can manipulate without worrying about reference changes!
        if (df_name in self.dfs):
            return self.dfs[df_name].df
        else:
            return None
        # why not self.dfs.get(df_name)?


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
        spec = gen_spec(df, get_chart_title(df_name))
        if spec:
            # set_data is false because gen_spec already sets the data
            return self.visualize_df_with_spec(df_name, spec, set_data=False)
        else:
            # TODO: add better explanations
            report_error_to_user("we could not generat the spec")


    # spec: VegaSpecType, encodings: Dict[Channel, str], chart_type: ChartType
    def visualize_df_with_spec(self, df_name: str, chart_info: ChartInfo, set_data=False):
        if (set_data):
            df = self.get_df(df_name)
            # note that we need to assign to a new variable, otherwise it will not load
            x_column = chart_info.encodings[Channel.x]
            y_column = chart_info.encodings[Channel.y]
            set_data_attr(chart_info.vega_spec, df, x_column, y_column)
        # register the spec to the df
        title = get_chart_title(df_name)
        w = MidasWidget(title, df_name, self.dfs[df_name].df_id, chart_info.vega_spec)
        # items[node.ind] = items[node.ind]._replace(v=node.v)
        vis = Visualization(chart_info, w)
        self.dfs[df_name] = self.dfs[df_name]._replace(visualization = vis)
        # note that we use a custom prefix to avoid accidentally overwrriting a user defined function
        cb = f"""
            var {CUSTOM_FUNC_PREFIX}val_str = JSON.stringify(value);
            var pythonCommand = `{MIDAS_INSTANCE_NAME}.js_add_selection("{df_name}", '${{{CUSTOM_FUNC_PREFIX}val_str}}')`;
            console.log("calling", pythonCommand);
            IPython.notebook.kernel.execute(pythonCommand)
        """
        w.register_signal_callback(SELECTION_SIGNAL, cb)
        out = ipywidgets.Output(layout={'border': '1px solid black'})

        with out:
          display(w)
        return w

    # ----------------------------------------------------------------------------
    # METHODS EXPOSED TO USERS
    # ----------------------------------------------------------------------------
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
        derivation = DFDerivation(df_name, new_df_name, DerivationType.loc, loc_spec)
        replace_index = False
        self.register_df(new_df, new_df_name, derivation, replace_index)
        return new_df


    def register_df(self, df: DataFrame, df_name: str, derivation=None, replace_index=True):
        """pivate method to keep track of dfs
            TODO: make the meta_data work with the objects
        """
        logging("register_df", df_name)
        created_on = datetime.now()
        selections: List[SelectionPredicate] = []
        chart_spec = None # to be populated later
        if replace_index:
            df.index = df.index.map(str).map(lambda x: f"{x}-{df_name}")
            df.index.name = CUSTOM_INDEX_NAME
        df_info = DFInfo(df_name, self._get_id(df_name), df, created_on, selections, derivation, chart_spec)
        self.dfs[df_name] = df_info
        self.__show_or_rename_visualization(df_name)
        if self.midas_cell_comm:
            self.midas_cell_comm.send({'name': df_name})

        return

    def register_series(self, series: Series, name: str):
        # turn it into a df
        df = series.to_frame()
        return self.register_df(df, name)

    def remove_df(self, df_name: str):
        self.dfs.pop(df_name)


    def read_json(self, path: str, df_name: str, **kwargs):
        check_path(path)
        df = read_json(path, kwargs)
        self.register_df(df, df_name)
        return df


    def read_csv(self, path: str, df_name: str, **kwargs):
        check_path(path)
        df = read_csv(path, kwargs)
        # meta_data = DfMetaData(time_created = datetime.now())
        # note that if it's via read_csv, it problably has a new index
        self.register_df(df, df_name)
        return df


    def _tick(self, df_name: str, history_index: int):
        self.tick_log.append(TickSpec(df_name, history_index, datetime.now()))
        logging("tick", f"processing {df_name} with history {history_index}")
        print("actually processing")
        self._process_tick(df_name, history_index)
        return

    def _process_tick(self, df_name: str, history_index: int):
        self.current_tick += 1
        df_info = self.dfs[df_name]
        if df_info is None:
            return
        _predicate = get_selection_by_predicate(df_info, history_index)

        if not _predicate:
            return
        # weird hack to make pyright happy...
        predicate = _predicate
        # TODO check if predicate the same as before
        lineage_data: DataFrame = None
        items = self.tick_funcs.get(df_name)
        logging("tick", f"for predicate{predicate}")
        def update_df(new_data: DataFrame, target_df: str):
            if (new_data is not None) and (len(new_data.index) > 0):
                # register data if this is the first time that this is called
                if not self._has_df(target_df):
                    self.register_df(new_data, target_df)
                else:
                    # see if we need to do any transforms..
                    vis_data = new_data
                    # we need to look up the target...
                    df_target_additional_transforms = self.dfs[target_df].visualization.chart_info.additional_transforms
                    if (df_target_additional_transforms == DfTransform.categorical_distribution):
                        first_col = new_data.columns.values[0]
                        vis_data = get_categorical_distribution(new_data[first_col], first_col)
                    elif (df_target_additional_transforms == DfTransform.numeric_distribution):
                        first_col = new_data.columns.values[0]
                        vis_data = get_numeric_distribution(new_data[first_col], first_col)

                    # update the data in store
                    self.set_df_data(target_df, new_data)
                    # send the update
                    vis = self.dfs[target_df].visualization
                    if vis:
                        vis.widget.replace_data(vis_data)
            else:
                report_error_to_user(f"Transformation result on {df_name} was empty")

        def process_item(lineage_data: DataFrame,
            output_type: TickIOType,
            param_type: TickIOType,
            _call: Union[PredicateCallback, DataFrameCallback,
                         DataFrameToDataFrameCallback, PredicateToDataFrameCallback],
            target_df: Optional[str] = None):
            if (output_type == TickIOType.data) and (not target_df):
                raise InternalLogicalError("target_df should be defined")
            if (param_type == TickIOType.data) and (lineage_data is None):
                    lineage_data = get_df_by_predicate(df_info.df, predicate)

            _target_df = target_df if target_df else "ERROR" # hack to make pyright happy
            if (output_type == TickIOType.data) and (param_type == TickIOType.data):
                new_data = _call(lineage_data)
                update_df(new_data, _target_df)
            elif (output_type == TickIOType.data) and (param_type == TickIOType.predicate):
                new_data = _call(lineage_data)
                update_df(new_data, _target_df)
            elif (output_type == TickIOType.void) and (param_type == TickIOType.predicate):
                return _call(predicate)
            elif (output_type == TickIOType.void) and (param_type == TickIOType.data):
                if lineage_data is None:
                    lineage_data = get_df_by_predicate(df_info.df, predicate)
                return _call(lineage_data)
            else:
                raise InternalLogicalError(f"not all cases handled: {output_type}, {param_type}")

        # now run
        if items:
            for _, i in enumerate(items):
                process_item(lineage_data, i.output_type, i.param_type, i.call, i.target_df)


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
            if predicate_raw:
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
            else:
                predicate = NullSelectionPredicate(interaction_time)

            history_index = len(df_info.predicates)
            df_info.predicates.append(predicate)
            return self._tick(df_name, history_index)
        else:
            print("Should already be defined")
            # raise InternalLogicalError
            return
        


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

    @staticmethod
    def help():
        print(HELP_INSTRUCTION)


    # decorator
    def bind(self, param_type: Union[TickIOType, str], output_type: Union[TickIOType, str], df_interact_name: str, target_df: Optional[str]=None):
        if not (self._has_df(df_interact_name)):
            raise DfNotFoundError(f"{df_interact_name} is not in the collection of {self.dfs.keys()}")
        if target_df and (target_df in self.dfs):
            raise UserError(f"Your result based df {df_interact_name} alread exists, please chose a new name")
        
        _param_type = cast(TickIOType, TickIOType[param_type] if (type(param_type) == str) else param_type)
        _output_type = cast(TickIOType, TickIOType[output_type] if (type(param_type) == str) else output_type)
        def decorator(call):
            nonlocal target_df
            if (_output_type == TickIOType.data) and (not target_df):
                rand_hash = get_random_string(4)
                target_df = f"{call.__name__}_on_{df_interact_name}_{rand_hash}"
            item = TickItem(_param_type, _output_type, call, target_df)
            self._add_to_tick(df_interact_name, item)
        return decorator


    def register_join_info(self, dfs: List[str], join_columns: List[str]):
        join_info = JoinInfo(dfs, join_columns)
        self.joins.append(join_info)


    def add_facet(self, df_name: str, facet_column: str):
        # 
        raise NotImplementedError()

    def js_get_current_chart_code(self, df_name: str) -> Optional[str]:
        # figure out how to derive the current df
        # don't have a story yet for complicated things...
        # decide on if we want to focus on complex code gen...
        if self._has_df(df_name):
            predicates = self.dfs[df_name].predicates
            if (len(predicates) > 0):
                predicate = predicates[-1]
                code = get_df_code(predicate, df_name)
                print(code)
                copy(code)
                return code
        # something went wrong, so let's tell comes...
        self.midas_cell_comm.send({
            'type': 'error',
            'value': f'no selection on {df_name} yet'
        })
        return

    def link(self, df1_name: str, df2_name: str):
        # infer how  df_interact_name and df_filter_name are connected to each other
        # the simplest case is that they are both columns from a large existing table
        # basically re-write the otherone if we know how to
        # then do similar as new_visualization_from_selection
        # use the predicate to link them together

        # case 1: two dfs derived from the same original df, both using loc
        #         then we can either create a new Vega spec with data, using loc
        #         or we can just go through the predicate construction via the df logic?
        #         #TODO: ask Arvind?
        # all we need to do now is to filter the target
        # 1. create a transform function

        # 2. create tick item
        df2_info = self.dfs[df2_name]
        df2 = df2_info.df
        df_transformation = get_df_transform_func_by_index(df2)
        # call = DataFrameCall(df_transformation, df2_name)
        target_df = df2_name
        item = TickItem(TickIOType.data, TickIOType.data, df_transformation, target_df)
        self._add_to_tick(df1_name, item)
        # update if there is already a selection
        df_info = self.dfs[df1_name]
        if (len(df_info.predicates) > 0):
            # register it
            new_data = df_transformation(get_df_by_predicate(df_info.df, df_info.predicates[-1]))
            df2_info.visualization.widget.replace_data(new_data)
        return


# def load_ipython_extension(ipython):
# # ip = get_ipython()
#     magics = Midas(ipython)
#     ipython.register_magics(magics)


__all__ = ['Midas']
