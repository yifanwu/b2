from enum import Enum
from functools import reduce
from typing import List, Union, Optional, NamedTuple, Dict, cast, Callable, Any
from datetime import datetime
import inspect
import asttokens
import ast
import operator
from datascience import Table, are

# for development
from IPython.core.debugger import set_trace
from midas.constants import MAX_BINS, MAX_DOTS, ISDEBUG

from midas.state_types import DFName
from midas.vis_types import EncodingSpec
from midas.util.errors import InternalLogicalError, UserError, NotAllCaseHandledError
from midas.util.utils import find_name, get_random_string, red_print
from midas.util.errors import type_check_with_warning, InternalLogicalError
from midas.vis_types import EncodingSpec, ENCODING_COUNT
from midas.showme import infer_encoding_helper

from .selection import SelectionType, SelectionValue, NumericRangeSelection, SetSelection, ColumnRef
from .data_types import DFId

# for adding documentation from datascience module despite the wrapper
def add_doc(value):
    def _doc(func):
        # processed_value = value.replace("Table()", "m")
        func.__doc__ = value
        return func
    return _doc

ColumnSelection = Union[str, List[str]]

class ColumnType(Enum):
    number = "number"
    time = "time"
    string = "string"
    boolean = "boolean"


# Note: we will have to put in some effort on creating this metadata when loading in DFs...
class TypedColumn(NamedTuple):
    name: str
    c_type: ColumnType


class RelationalOpType(Enum):
    where = "where"
    project = "project"
    join = "join"
    groupby = "groupby"
    aggregation = "aggregation"
    base = "base"


class JoinPredicate(object):
    """[summary]
    
    Arguments:
        object {[type]} -- [description]
    """
    def __init__(self, left_col: ColumnRef, right_col: ColumnRef):
        self.left_col = left_col
        self.right_col = right_col



class Predicate(object):
    def __init__(self, column_or_label, value_or_predicate, other=None):
        self.column_or_label = column_or_label
        self.value_or_predicate = value_or_predicate
        self.other = other

    def __repr__(self):
        other = f", other: {self.other}" if self.other is not None else ""
        return f"column_or_label: {self.column_or_label}, value_or_predicate: {self.value_or_predicate}{other}"


class JoinInfo(object):
    # left_df: 'MidasDataFrame'
    # right_df: 'MidasDataFrame'
    columns: List[JoinPredicate]
    def __init__(self, left_df: 'MidasDataFrame', right_df: 'MidasDataFrame', columns: List[JoinPredicate]):
        self.left_df = left_df
        self.right_df = right_df
        self.columns = columns
    
    def swap_left_right(self):
        columns = []
        for c in self.columns:
            columns.append(JoinPredicate(c.right_col, c.left_col))
        return JoinInfo(self.right_df, self.left_df, columns)
        




# FIXME: think about how to make this less clunky --- seems that this has to be constantly passed around
class RuntimeFunctions(NamedTuple):
    add_df: Callable[['MidasDataFrame'], None]
    create_with_table_wrap: Callable[[Table, str], 'MidasDataFrame']
    show_df: Callable[['MidasDataFrame', EncodingSpec, Optional[bool]], None]
    # show_df_filtered: Callable[['MidasDataFrame', DFName], None]
    # show_profiler: Callable[['MidasDataFrame'], None]
    get_filtered_df: Callable[[str], Optional['MidasDataFrame']]
    # get_stream: Callable[[DFName], MidasSelectionStream] 
    apply_other_selection: Callable[['MidasDataFrame', List[SelectionValue]], Optional['MidasDataFrame']]
    add_join_info: Callable[[JoinInfo], None]


class NotInRuntime():
    pass


class MidasDataFrame(object):
    """A Midas dataframe is a 

    Here is a list of useful functions
    >> 
    """
    _id: DFId
    _df_name: Optional[DFName]
    _rt_funcs: RuntimeFunctions
    _ops: 'RelationalOp' # type: ignore
    # the following is used for code gen
    _suggested_df_name: Optional[str]
    current_filtered_data: Optional['MidasDataFrame']

    def __init__(self,
      ops: 'RelationalOp',
      rt_funcs: RuntimeFunctions,
      table: Optional[Table] = None,
      df_name: str = None,
      df_id: DFId = None,
      is_base: bool = False,
      ):
        self._ops = ops
        self._table = table
        self._rt_funcs = rt_funcs
        if df_id:
            self._id = df_id
        else:
            self._id = DFId(get_random_string(5))
        if df_name is not None:
            self.df_name = DFName(df_name)
        else:
            df_name_raw = find_name()
            if df_name_raw:
                self.df_name = DFName(df_name_raw)
        if hasattr(self, "df_name") and (self.df_name is not None):
            self._rt_funcs.add_df(self)

    #################
    # Magic Methods #
    #################
    #  extended from the datascience module

    def __getitem__(self, index_or_label):
        return self.table.column(index_or_label)

    def __setitem__(self, index_or_label, values):
        self.append_column(index_or_label, values)

    def __getattr__(self, name: str) -> Any:
        DATA_SCIENCE_MODULE_FUNS = [
            # the following are accessors and do NOT return dataframes
            "num_rows",
            "row",
            "labels",
            "num_columns",
            "column",
            "values",
            "column_index",
            # plotting
            "plot",
            "bar",
            "group_bar",
            "barh",
            "group_barh",
            "scatter",
            "hist",
            "hist_of_counts",
            "boxplot",
            # exporting
            "to_csv",
            "to_df",
            # mutations
            "sort",
            "drop",
            "relabel",
            "append_column",
            "append",
            "set_format",
            "move_to_start",
            "move_to_end",
            "remove",
            # returns a df but is no longer managed by midas
            "copy"
        ]
        if name in DATA_SCIENCE_MODULE_FUNS:
            return getattr(self.table, name)
        elif name == "_repr_html_":
            return self.table._repr_html_
        elif name == "df_name":
            return
        elif name[0] == "_":
            # "_ipython_canary_method_should_not_exist_", "_repr_markdown_", "_repr_pdf_", "_ipython_display_", "_repr_jpeg_"
            return
        elif name == "items":
            # this appears also to be another one of the python things?
            return
        else:
            red_print(f"The dataframe function, {name}, does not exist--note that we do not support all methods in the datascience module. If you want to access the columns, please use `df_name['column_name']` to access, instead of attribute.")


    def __repr__(self):
        return self.table.__repr__()

    def __str__(self):
        return self.table.__str__()

    @classmethod
    def create_with_table(cls, table: Table, df_name_raw: Optional[str], midas_ref):
        if df_name_raw is None:
            raise UserError("Please assign a variable to the table returned!")
        
        df_name = DFName(df_name_raw)
        df_id = DFId(get_random_string(5))
        ops = BaseOp(df_name, df_id, table)
        df = cls(ops, midas_ref, table, df_name, df_id, is_base=True)
        # df.show_profile()
        return df

    def new_df_from_ops(self, ops: 'RelationalOp', table: Optional[Table]=None, df_name: Optional[str] = None):
        return MidasDataFrame(ops, self._rt_funcs, table, df_name)


    @property
    def table(self) -> Table:
        if hasattr(self, "_table") and (self._table is not None):
            return self._table
        else:
            table = eval_op(self._ops)
            self._table = table
            return table


    @property
    def columns(self) -> List[TypedColumn]:
        # assuming the table is not empty
        values = self.table.rows[0]
        column_strs = self.table.labels
        columns: List[TypedColumn] = []
        for c in column_strs:
            value = values.__getattr__(c)
            if isinstance(value, str):
                columns.append(TypedColumn(c, ColumnType.string))
            elif isinstance(value, bool):
                columns.append(TypedColumn(c, ColumnType.boolean))
            elif isinstance(value, datetime):
                columns.append(TypedColumn(c, ColumnType.time))
            else:
                columns.append(TypedColumn(c, ColumnType.number))
        return columns

    # IDEA: some memorized functions to access the DF's statistics
    # e.g., https://dbader.org/blog/python-memoization


    def rows(self, idx: int):
        return self.table.rows(idx)

    @add_doc(Table.sample.__doc__)
    def sample(self, k: int):
        """function to sample dataframes
        - if the name is assigned, it will be registered as an original table
        - if there is no name, the dataframe is printed
        
        Arguments:
            k {int} -- size of the sample
        """
        new_df = self.table.sample(k)
        try:
            df_name = find_name()
            if df_name:
                new_df.df_name = df_name
                return self._rt_funcs.create_with_table_wrap(new_df, df_name)
            return new_df
        except UserError as err:
            return new_df

        # let's register this 

    @add_doc(Table.column.__doc__)
    def column(self, col_name: str):
        return self.table[col_name]


    @add_doc(Table.select.__doc__)
    def select(self, columns: List[str]) -> 'MidasDataFrame':
        new_table = self.table.select(columns)
        new_ops = Select(columns, self._ops)
        df_name = find_name(False)
        return self.new_df_from_ops(new_ops, new_table, df_name)


    @add_doc(Table.where.__doc__)
    def where(self, column_or_label, value_or_predicate=None, other=None):
        new_table = self.table.where(column_or_label, value_or_predicate, other)
        predicate = Predicate(column_or_label, value_or_predicate, other)
        new_ops = Where(predicate, self._ops)
        df_name = find_name(False)
        return self.new_df_from_ops(new_ops, new_table, df_name)


    @add_doc(Table.join.__doc__)
    def join(self, column_label, other: 'MidasDataFrame', other_label):
        new_table = self.table.join(column_label, other.table, other_label)
        new_ops = Join(column_label, other, other_label, self._ops)
        df_name = find_name(False)
        return self.new_df_from_ops(new_ops, new_table, df_name)
    

    @add_doc(Table.group.__doc__)
    def group(self, column_or_label: ColumnSelection, collect=None):
        new_table = self.table.groups(column_or_label, collect)
        new_ops = GroupBy(column_or_label, collect, self._ops)
        df_name = find_name(False)
        return self.new_df_from_ops(new_ops, new_table, df_name)

    @add_doc(Table.apply.__doc__)
    def apply(self, fn, *column_or_columns):
        return self.table.apply(fn, *column_or_columns)


    # def show_profile(self):
    #     self._rt_funcs.show_profiler(self)


    def get_filtered_data(self):
        """returns the currently filtered data
        """
        return self._rt_funcs.get_filtered_df(self.df_name)


    def get_code(self):
        """returns the code used to generate the current dataframe
        """
        return get_midas_code(self._ops)


    def vis(self, **kwargs):
        """Shows the visualization in the Midas pannel
        Arguments:
            mark {str} -- "bar" | "circle" | "line"
            x {str} -- column for x axis
            x_type {str} -- "ordinal" | "quantitative" | "temporal"
            y {str} -- column for y axis
            y_type {str} -- "ordinal" | "quantitative" | "temporal"
            selection_type {str} -- "none", "multiclick", "brush"
            selection_dimensions {str} -- "none", "multiclick", "brush"
           
        Returns:
            DataFrame (so you can chain your functions)
        Raises:
            UserError: wehen the keyword arguments do not match the expected EncodingSpec
        """
        # if ISDEBUG: set_trace()
        spec = parse_encoding(kwargs, self)
        if spec:
            sanity_check_spec_with_data(spec, self)
            self._rt_funcs.show_df(self, spec, True)
        return self


    def reactive_vis(self, **kwargs):
        """This function is called inplace of `vis` for reactive cells, whose participation in the event loop is different from the others.
        """
        spec = parse_encoding(kwargs, self)
        if spec:
            sanity_check_spec_with_data(spec, self)
            self._rt_funcs.show_df(self, spec, False)
        return self

    
    def can_join(self, other_df: 'MidasDataFrame', col_name: str,col_name_other: Optional[str]=None):
        # assume that the joins are the same name!
        if self.df_name and other_df.df_name:
            if col_name_other:
                columns = [JoinPredicate(ColumnRef(col_name, self.df_name), ColumnRef(col_name_other, other_df.df_name))]
            else:
                columns = [JoinPredicate(ColumnRef(col_name, self.df_name), ColumnRef(col_name, other_df.df_name))]
            join_info = JoinInfo(self, other_df, columns)
            self._rt_funcs.add_join_info(join_info)
        else:
            raise UserError("DF not defined")



    def apply_selection(self, all_predicates: List[SelectionValue]):
        # if all the selections are null then reply nothing
        if len(all_predicates) == 0:
            return None
        return self._rt_funcs.apply_other_selection(self, all_predicates)


    def apply_self_selection_value(self, predicates: List[SelectionValue]):
        executable_predicates = list(map(create_predicate, predicates))
        return self.apply_predicates(executable_predicates)
        
    def apply_predicates(self, predicates: List[Predicate]) -> 'MidasDataFrame':
        # each predicate becomes a where clause, and we can chain them
        new_df = self
        for p in predicates:
            new_df = new_df.where(p.column_or_label, p.value_or_predicate, p.other)
        return new_df
        
    def _set_current_filtered_data(self, mdf: Optional['MidasDataFrame']):
        self.current_filtered_data = mdf

    # not currently used, but might be helpful in the future
    # @property
    # def is_base_df(self) -> bool:
    #     return self._ops.op_type == RelationalOpType.base # type: ignore


class RelationalOp(object):
    # chilren
    op_type: RelationalOpType
    child: 'RelationalOp'  # type: ignore

    def has_child(self):
        if hasattr(self, "child") and (self.child is not None):
            return True
        return False
    pass


class BaseOp(RelationalOp):
    def __init__(self, df_name: DFName, df_id: DFId, table: Table):
        self.op_type = RelationalOpType.base
        self.df_name = df_name
        self.df_id = df_id
        self.table = table
    
    def __repr__(self):
        return f"{{{self.op_type.value}: '{self.df_name}'}}"
    def __str__(self):
        return self.__repr__()

class Select(RelationalOp):
    def __init__(self, columns: ColumnSelection, child: RelationalOp):
        self.op_type = RelationalOpType.project
        self.columns = columns
        self.child = child
    
    def __repr__(self):
        return f"{{{self.op_type.value}: {{columns:{self.columns}, of: {self.child}}}}}"


class GroupBy(RelationalOp):
    def __init__(self, columns: ColumnSelection, collect, child: RelationalOp):
        self.op_type = RelationalOpType.groupby
        self.columns = columns
        self.collect = collect
        self.child = child

    def __repr__(self):
        return f"{{{self.op_type.value}: {{columns:{self.columns}, collect:{self.collect}, child: {self.child}}}}}"

class Where(RelationalOp):
    def __init__(self, predicate: Predicate, child: RelationalOp):
        self.op_type = RelationalOpType.where
        self.predicate = predicate
        self.child = child
    
    def __repr__(self):
        return f"{{{self.op_type.value}: {{predicate:{self.predicate}, of: {self.child}}}}}"



class Join(RelationalOp):
    """[summary]
    
    Arguments:
        self_columns {ColumnSelection} -- columns of the df to join on
        other {MidasDataFrame} -- other df
        other_columns {ColumnSelection} -- column from other df
        child {RelationalOp} -- previous operation that produces "self"
    
    note that other is a MidasDataFrame because at code gen time we need to knwo their names (but this is not the case for the self. #FIXME seems weird)
    """
    def __init__(self, self_columns: ColumnSelection, other: MidasDataFrame, other_columns: ColumnSelection, child: RelationalOp):
        self.op_type = RelationalOpType.join
        self.self_columns = self_columns
        self.other = other
        self.other_columns = other_columns
        self.child = child


    def __repr__(self):
        return f"{{{self.op_type.value}: {{left: {self.child}, right: {self.other._ops}, on: {self.self_columns},{self.other_columns}}}}}"


# Note, place here because of cyclic imports : (
class DFInfo(object):
    def __init__(self, df: MidasDataFrame):
        # df is the immediate df that might be filtered by each tick
        self.df = df
        self.created_on = datetime.now()
        self.df_type = "original"

    # def update_df(self, df: Optional[MidasDataFrame]) -> bool:
    #     raise InternalLogicalError("Should not attempt to update base dataframes")


class VisualizedDFInfo(DFInfo):
    def __init__(self, df: MidasDataFrame):
        if not df.df_name:
            raise InternalLogicalError("Visualized dfs must have df_names")
        self.df = df
        self.created_on = datetime.now()
        self.df_name = df.df_name
        # original df is that which was defined at the beginning
        self.original_df = df
        self.df_type = "visualized"
        # self.predicates: List[SelectionEvent] = []
        
    def update_df(self, df: Optional[MidasDataFrame]) -> bool:
        """
        Arguments:
            df {MidasDataFrame} -- the dataframe to be updated with
        Returns:
            bool -- whether the dataframe has changed
        """
        if df is not None and self.df is not None and self.df._id == df._id:
            return False
        
        self.df = df
        return True

    def __repr__(self) -> str:
        return f"df_info for {self.original_df.df_name}"



def get_midas_code(op: RelationalOp) -> str:
    if op.op_type == RelationalOpType.base:
         b_op = cast(BaseOp, op)
         return b_op.df_name
    else:
        prev_table = get_midas_code(op.child)

        if op.op_type == RelationalOpType.where:
            s_op = cast(Where, op)
            col_or_label = convert_value_or_predicate(
              s_op.predicate.column_or_label
            )

            val_or_pred = convert_value_or_predicate(
              s_op.predicate.value_or_predicate
            )

            other = convert_value_or_predicate(
              s_op.predicate.other
            )

            new_table = f"{prev_table}.where({col_or_label}, {val_or_pred}, {other})"
            return new_table
        if op.op_type == RelationalOpType.project:
            p_op = cast(Select, op)
            new_table = f"{prev_table}.select({p_op.columns!r})"
            return new_table
        if op.op_type == RelationalOpType.groupby:
            g_op = cast(GroupBy, op)
            new_table = f"{prev_table}.group({g_op.columns!r}, {get_lambda_declaration_or_fn_name(g_op.collect)})"
            return new_table
        if op.op_type == RelationalOpType.join:
            j_op = cast(Join, op)
            join_prep_code = ""
            # we assume that the other has data!
            if j_op.other.df_name is not None:
                other_df_name = j_op.other.df_name
            else:
                if not(hasattr(j_op.other, "_suggested_df_name") or hasattr(j_op.other._suggested_df_name, "_suggested_df_name")):
                    raise InternalLogicalError("the join df should have a suggested name")
                ops_code = get_midas_code(j_op.other._ops)
                join_prep_code = f"{j_op.other._suggested_df_name} = {ops_code}"
                other_df_name = j_op.other._suggested_df_name
            new_table = f"{join_prep_code}\n{prev_table}.join({j_op.self_columns!r}, {other_df_name}, {j_op.other_columns!r})"
            return new_table
        else:
            raise NotImplementedError(op.op_type)   


def convert_value_or_predicate(val_or_pred) -> str:
    """Convert a value or predicate into a code string.

    val_or_red: intended to be a function or callable from the
    datascience.predicates module
    """
    if val_or_pred is None:
        return "None" 
    elif inspect.getmodule(val_or_pred) and inspect.getmodule(val_or_pred).__name__ == 'datascience.predicates':
        # Get the parameters of the predicate
        closure_vars = inspect.getclosurevars(val_or_pred.f).nonlocals

        # Create the assignment of parameters
        assignments = ", ".join(f"{k}={v}" for k, v in closure_vars.items())

        _, line_no = inspect.getsourcelines(val_or_pred)
        lines, _ = inspect.findsource(inspect.getmodule(val_or_pred))
        atok = asttokens.ASTTokens("".join(lines), parse=True)

        # Consider the possible predicate functions this could be
        function_nodes = filter(
          lambda node: isinstance(node, ast.FunctionDef)
                       and node.lineno < line_no, ast.walk(atok.tree)
        )

        # The correct predicate function has the greatest line number
        # smaller than the lineno (lineno is a line number of a line of code
        # within the correct predicate function)
        f = max(function_nodes, key=operator.attrgetter("lineno")).name # type: ignore

        return f"m.are.{f}({assignments})"
    elif inspect.isfunction(val_or_pred):
        return get_lambda_declaration_or_fn_name(val_or_pred)
    else:
        return repr(val_or_pred)


def get_lambda_declaration_or_fn_name(fn: Callable) -> str:
    if fn is None:
        return "None" 
    if fn.__name__ == "<lambda>":
        source = inspect.getsource(fn)
        atok = asttokens.ASTTokens(source, parse=True)
        attr_node = next(n for n in ast.walk(atok.tree) if isinstance(n, ast.Lambda))
        start, end = attr_node.first_token.startpos, attr_node.last_token.endpos # type: ignore
        return source[start: end]
    else:
        return fn.__name__


def eval_op(op: RelationalOp) -> Optional[Table]:
    # note that some of the ops would simply return 
    if op.op_type == RelationalOpType.base:
        b_op = cast(BaseOp, op)
        return b_op.table
    else:
        prev_table = eval_op(op.child)
        if not prev_table:
            return None

        if op.op_type == RelationalOpType.where:
            s_op = cast(Where, op)
            new_table = prev_table.where(s_op.predicate.column_or_label, s_op.predicate.value_or_predicate, s_op.predicate.other)
            return new_table
        if op.op_type == RelationalOpType.project:
            p_op = cast(Select, op)
            new_table = prev_table.select(p_op.columns)
            return new_table
        if op.op_type == RelationalOpType.groupby:
            g_op = cast(GroupBy, op)
            new_table = prev_table.group(g_op.columns, g_op.collect)
            return new_table
        if op.op_type == RelationalOpType.join:
            j_op = cast(Join, op)
            new_table = prev_table.join(j_op.self_columns, j_op.other.table, j_op.other_columns)
            return new_table
        else:
            raise NotImplementedError(op.op_type)


def create_predicate(s: SelectionValue) -> Predicate:
    col_name = s.column.col_name
    # if s.selection_type == SelectionType.single_value:
    #     sv = cast(SingleValueSelection, s)
    #     return Predicate(col_name, sv.val)
    if s.selection_type == SelectionType.numeric_range:
        nv = cast(NumericRangeSelection, s)
        p_func = are.between_or_equal_to(nv.minVal, nv.maxVal)
        return Predicate(col_name, p_func)
    elif s.selection_type == SelectionType.string_set:
        ssv = cast(SetSelection, s)
        p_func = are.contained_in(ssv.val)
        return Predicate(col_name, p_func)
    else:
        raise NotAllCaseHandledError(f"Got {s.selection_type}, and we only support {SelectionType.string_set}, {SelectionType.numeric_range}, and {SelectionType.single_value}")

# helper tables placed here due to import issues

def get_selectable_column(mdf: MidasDataFrame):
    # if anything is the result of groupby aggregation
    columns_grouped = []
    def walk(ops: RelationalOp):
        if ops.op_type == RelationalOpType.groupby:
            g_op = cast(GroupBy, ops)
            # g_op.columns is a union type of str and array of strings (for developer convenience)
            # FIXME: maybe just make everything array of strings instead...
            if isinstance(g_op.columns, str):
                columns_grouped.append(set([g_op.columns]))
            else:
                columns_grouped.append(set(g_op.columns))
        if ops.has_child():
            walk(ops.child)
        else:
            return
    walk(mdf._ops)
    final_columns = mdf.table.labels
    if len(columns_grouped) > 0:
        original_columns = reduce(lambda a, b: a.intersection(b), columns_grouped)
        result = original_columns.intersection(set(final_columns))
        return result
    else:
        # no groupby, great, all the things are fine
        return final_columns

def sanity_check_spec_with_data(spec, df):
    # TODO: add some constrains for bad configurations
    num_rows = df.num_rows
    if spec.mark == "bar" and num_rows > MAX_BINS:
        raise UserError("Too many categories for bar chart to plot. Please consider grouping.")
    elif num_rows > MAX_DOTS:
        raise UserError("Too many points to plot")
    return


def parse_encoding(kwargs, df):
    if len(kwargs) == 0:
        return infer_encoding(df)
    elif len(kwargs) < ENCODING_COUNT:
        encoding = infer_encoding(df).__dict__
        for k in kwargs:
            encoding[k] = kwargs[k]
        # print("encodings", encoding)
        return EncodingSpec(**encoding)
    else:
        try:
            spec = EncodingSpec(**kwargs)
        except TypeError as error:
            e = f"{error}"[11:]
            raise UserError(f"Arguments expected: {e}, and you gave {kwargs}")
    
def infer_encoding(mdf: MidasDataFrame) -> Optional[EncodingSpec]:
    """Implements basic show me like feature"""
    df = mdf.table
    type_check_with_warning(df, Table)
    selectable = get_selectable_column(mdf)
    is_groupby = mdf._ops.op_type == RelationalOpType.groupby
    return infer_encoding_helper(mdf, selectable, is_groupby)