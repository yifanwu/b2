from midas.midas_algebra.dataframe import MidasDataFrame
from midas.state_types import DFName
from typing import List, Union
from .midas_algebra.selection import SelectionValue
from .midas import Midas

class MidasSelection(object):
    # wrap around the selections
    values: List[SelectionValue]
    # when it was selected
    # what df
    # maybe where it can link to etc?
    def __init__(self, ref: Midas, values: List[SelectionValue]):
        self.midas = ref
        self.values = values
    
    def apply_to(self, df: Union[DFName, MidasDataFrame]):
        # this returns a MidasDataFrame
        self.midas.



class MidasSelectionStream(object):
    """[An obeserver object that ]
    
    Arguments:
        object {[type]} -- [description]
    """
    midas: Midas

    def __init__(self, ref: Midas, df_name: DFName):
        self.midas = ref
        self.df_name = df_name

    def get_current(self):
        return self.midas.state.get_df(self.df_name)



