from typing import Dict, List
import traceback
import pandas as pd

from .types import JoinInfo, OpLogItem, OpType
from .state import State
from .util.parsing import get_assignment_name


class Context(object):
    """Context captures passively the context from pandas
    as well as information provided by the user
    
    """
    state: State
    joins: List[JoinInfo]
    op_log: List[OpLogItem]
    
    def __init__(self, state: State):
        self.joins = []
        self.state = state
        self.op_log = []

    def decorate_pandas(self):
        #####################################
        def _decorate_df_loader(fun_name: str):
            old_name = f"_{fun_name}_old"
            setattr(pd, old_name, getattr(pd, fun_name))
            def decorate_df(df, user_df_name):
                print(df)
                df._m = {"user_df_name": user_df_name};
            def loader(*args, **kwargs):
                new_df = pd[old_name](*args, **kwargs)
                prev_line = traceback.format_stack()[-2]
                code = prev_line.splitlines()[1]
                user_df_name = get_assignment_name(code)
                op = OpLogItem(
                    op=OpType.load,
                    src_name=None,
                    fun_name=fun_name,
                    dest_name=user_df_name,
                    args= args,
                    kwargs= kwargs)
                self.op_log.append(op)
                df_name = decorate_df(new_df, user_df_name)
                self.state.add_df(new_df, df_name)
                return new_df            
            setattr(pd, fun_name, loader)

        # now actually call them!
        loader_funs = ["read_cvs", "read_json"]
        [_decorate_df_loader(f) for f in loader_funs]

        #####################################
        # decorate loc
        # TODO for Ryan
        # get the following cases
        # 