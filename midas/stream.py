from midas.state_types import DFName
from midas.vis_types import SelectionPredicate
from typing import NewType, Callable, Union, List, Any

# class MidasSelection(object):
# # wrap around the selections
# values: List[SelectionValue]
# # when it was selected
# # what df
# # maybe where it can link to etc?
# def __init__(self, ref: Midas, values: List[SelectionValue]):
#     self.midas = ref
#     self.values = values

# def apply_to(self, df: Union[DFName, MidasDataFrame]):
#     # this returns a MidasDataFrame
#     self.midas.


TickId = NewType('TickId', str)

class MidasSelectionStream(object):
    """An obeserver object that 
    
    Arguments:
        object {[type]} -- [description]
    """

    # FIXME: add function typing
    def __init__(self,
        df_name: DFName,
        ref_to_predicate_list: List[SelectionPredicate],
        bind: Callable[[DFName, Any], Any]
      ):
        self.ref_to_predicate_list = ref_to_predicate_list
        self.df_name = df_name
        self.bind = bind

    @property
    def current(self):
        if (len(self.ref_to_predicate_list) > 0):
            return self.ref_to_predicate_list[-1]
        else:
            return None


    @property
    def history(self):
        raise NotImplementedError()
        # return self.get_history(self.df_name)


    # FIXME: not sure how better to name these # NAMING
    def add_callback(self, cb) -> TickId:
        return self.bind(self.df_name, cb)




