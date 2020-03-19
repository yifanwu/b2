from copy import deepcopy, copy
from typing import List,  Dict, Optional, cast, Tuple
from collections import defaultdict
# for development
from IPython.core.debugger import set_trace

from midas.util.errors import InternalLogicalError, debug_log
from midas.util.errors import InternalLogicalError
from midas.state_types import DFName

from .dataframe import RelationalOpType, MidasDataFrame, BaseOp, RelationalOp, DFInfo, VisualizedDFInfo, Where, JoinInfo, Select, create_predicate, Join
from .selection import SelectionValue
from midas.constants import ISDEBUG

class Context(object):
    # dfs: Dict[DFName, DFInfo]
    join_info: Dict[Tuple[DFName, DFName], JoinInfo]
    # store it for easier df gen...

    def __init__(self, df_info_store: Dict[DFName, DFInfo], new_df_from_ops):
        """[summary]
        
        Arguments:
            get_dfs {Callable[[], List[MidasDataFrame]]} -- passed from state so that they share access to the up tp date state
        """
        self.df_info_store = df_info_store
        self.join_info = {}
        self.new_df_from_ops = new_df_from_ops


    def get_df(self, df_name: DFName) -> MidasDataFrame:
        found = self.df_info_store[df_name]
        if found:
            if isinstance(found, VisualizedDFInfo):
                return found.original_df
            else:
                return found.df
        else:
            raise InternalLogicalError(f"DF {df_name} not found")


    # takes in joinable columns on a left and right df, adds this information into our join_info dictionary
    # consider making it easier to enter
    def add_join_info(self, joins: JoinInfo):
        left_df = joins.left_df
        right_df = joins.right_df
        if left_df.df_name is not None and right_df.df_name is not None: # type: ignore
            self.join_info[(left_df.df_name, right_df.df_name)] = joins # type: ignore
            self.join_info[(right_df.df_name, left_df.df_name)] = joins.swap_left_right() # type: ignore
        else:
            raise InternalLogicalError("The DFs with join info should have df_names")
    
    
    # takes in a left_df and right_df, and returns all possible column names for them to be joined on
    # def get_join_info(self, left_df: MidasDataFrame, right_df: MidasDataFrame):
    #     if left_df.df_name is not None and right_df.df_name is not None:
    #         return 
    #     else:
    #         raise InternalLogicalError("should have df_names")


    def apply_join_selection(self, join_info: JoinInfo, selections: List[SelectionValue]) -> RelationalOp:
        """
        Arguments:
            join_info {JoinInfo} -- Note that the left one is the "original base" and the right is the one joined
            selections {List[SelectionValue]} -- [description]
        
        Raises:
            NotImplementedError: if there are more than on ecolumn, do not handle for now.
        
        Returns:
            RelationalOp -- [description]
        """
        # if ISDEBUG: set_trace()
        # we know that join info must base baseop
        new_ops = cast(BaseOp, deepcopy(join_info.right_df._ops)) # type: ignore
        filtered_join_df = apply_non_join_selection(new_ops, selections)
        if len(join_info.columns) > 1:
            raise NotImplementedError("Currently not supported")
        base_col = join_info.columns[0].left_col.col_name
        join_col = join_info.columns[0].right_col.col_name
        index_column_df = self.new_df_from_ops(Select(join_col, filtered_join_df))
        # we must assign something
        selection_columns = "_".join([s.column.col_name for s in selections])
        index_column_df._suggested_df_name = f"{new_ops.df_name}_filtered_{selection_columns}"
        # then do the join
        # TODO: better to do the "in" operations        
        new_base = deepcopy(join_info.left_df._ops) # type: ignore
        final_ops = Join(base_col, index_column_df, join_col, new_base)
        # if ISDEBUG: set_trace()
        return final_ops

    # get a bunch of bases and decide where the column comes from 
    # we might have 2 here, and we need to decide which one to pick
    #   based on the column names, this is easy if 
    # Joins have a certain behaviors in datascience that
    #   makes it hard to reason about which column things came from,
    #   for now, let’s just give up. :(, maybe @shloak can take a stab? #TODO/FIXME
    def get_base_df_selection(self, s: SelectionValue) -> Optional[SelectionValue]:
        # look up df
        df = self.get_df(s.column.df_name)
        bases = find_all_baseops(df._ops)

        def find_base_with_column(bases: List[BaseOp]):
            for b in bases:
                a_df = self.get_df(b.df_name)

                # LEAKY abstraction --- indirectly depending on tables...
                if s.column.col_name in a_df.table.labels:
                    # we are done
                    return b
        base_op = find_base_with_column(bases)
        new_selection = deepcopy(s)
        if (base_op):
            new_selection.column.df_name = base_op.df_name
            return new_selection
        else:
            return None
            # raise InternalLogicalError(f"base selection should have been found for {s.column.df_name}filtered by columns {s.column.col_name}")


    def apply_selection(self, target_df: MidasDataFrame, selections: List[SelectionValue], is_union=False) -> Optional[MidasDataFrame]:
        if len(selections) == 0:
            return None
        # before we do any of that, just check to see if the filter is directly on the target_df itself?
        selections_on_base = map(self.get_base_df_selection, selections)
        selections_by_df = defaultdict(list)
        for s in selections_on_base:
            # note that if something is not found, we simply ignore it
            # this sometimes happens when we miscategorize.
            if s is not None:
                selections_by_df[s.column.df_name].append(s)
        
        if target_df.df_name in selections_by_df:
            raise InternalLogicalError(f"Shouldn't be using context to do the filter if the two DFs are the same, we got {target_df.df_name} as target, which is in {selections_by_df.keys()}")

        new_ops = target_df._ops
        # it doesn't really matter what order we apply these in
        for df_name in selections_by_df.keys():
            new_ops = self.apply_selection_from_single_df(new_ops, df_name, selections_by_df[df_name])  # type: ignore
        new_df = target_df.new_df_from_ops(new_ops) # type: ignore
        return new_df


    def find_joinable_base(self, current_bases: List[BaseOp], selection_base_df: DFName) -> Optional[JoinInfo]:
        """
        note that the current_base is left_df, and the base to join with is right_df
        """
        for b in current_bases:
            r = self.join_info.get((b.df_name, selection_base_df))
            if r is not None:
                return r
        return None


    def apply_selection_from_single_df(self, ops: RelationalOp, df_name: DFName, selections: List[SelectionValue]) -> RelationalOp:
        # here we can assume that all the selections have the same df
        bases = find_all_baseops(ops)
        # see if the selection list has anything in the bases
        non_join_base_list = list(filter(lambda b: b.df_name == df_name, bases))
        if len(non_join_base_list) > 0:
            non_join_base = non_join_base_list[0]
            local_base_df_name = non_join_base.df_name
            replacement_op = apply_non_join_selection(non_join_base, selections)
        else:
            # search for which one we can actually join with 
            r = self.find_joinable_base(bases, df_name)
            if r:
                # it's always the right one (by construct)
                local_base_df_name = r.left_df.df_name
                replacement_op = self.apply_join_selection(r, selections)
            else:
                # NO OP
                if ISDEBUG:
                    debug_log(f"No op for {df_name} selection because no join was found")
                return ops

        # 2. apply the replacement
        if replacement_op and local_base_df_name:
            return set_if_eq(deepcopy(ops), replacement_op, local_base_df_name)
        raise InternalLogicalError("Replacement Op is not set or the df_name is not set")


####################################
########    helper funcs    ########
####################################

def set_if_eq(original: RelationalOp, replacement: RelationalOp, df_name: DFName):
    should_return_replacement = False
    # note that we need the special casing because of the special case
    def _helper(op: RelationalOp, new_op: RelationalOp, parent_op: Optional[RelationalOp]):
        if (op.op_type == RelationalOpType.base):
            base_op = cast(BaseOp, op)
            if (base_op.df_name == df_name):
                # if parent_op is not defined, then we are literally replacing
                if parent_op is None:
                    should_return_replacement = True
                    return
                else:
                    parent_op.child = new_op
                    return
        elif (op.has_child()):
            return _helper(op.child, new_op, op)
        else:
            raise InternalLogicalError("Should either have child or be of base type")
    
    _helper(original, replacement, None)
    if should_return_replacement:
        return replacement
    else:
        return original

    

def find_all_baseops(op: RelationalOp) -> List[BaseOp]:
    """takes the source op and returns all the baseops
       e.g. given that df and df2 are loaded in as external data,
            then the op representing `df.join("id", df2, "id")select(["sales"])`
            will return df and df2's respective `baseop`s.
    
    Arguments:
        op {RelationalOp} -- [description]
    
    Returns:
        List[BaseOp] -- [description]
    """
    if (op.op_type == RelationalOpType.base):
        base_op = cast(BaseOp, op)
        return [base_op]
    if (op.op_type == RelationalOpType.join):
        join_op = cast(Join, op)
        b1 = find_all_baseops(op.child)
        b2 = find_all_baseops(join_op.other._ops)
        return b1 + b2
    if (op.has_child()):
        return find_all_baseops(op.child)
    else:
        return []


def apply_non_join_selection(ops: BaseOp, selections: List[SelectionValue]) -> RelationalOp:
    # it has to be BaseOp because it's used to generate the df to be replaced
    executable_predicates = list(map(create_predicate, selections))
    new_ops = copy(ops)
    for p in executable_predicates:
        new_ops = Where(p, new_ops)
    return new_ops

