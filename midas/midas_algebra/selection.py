from midas.util.errors import InternalLogicalError
from midas.state_types import DFName

from typing import Union, cast, Set
from enum import Enum
import json

# note that Column ref is different from 
class ColumnRef(object):
    
    def __init__(self, col_name: str, df_name: DFName):
        self.col_name = col_name
        self.df_name = df_name

    def __eq__(self, other: 'ColumnRef'):
        if self.col_name != other.col_name:
            return False
        if self.df_name != other.df_name:
            return False
        return True

    def __repr__(self):
        return f"{{col_name: '{self.df_name}',  df_name: '{self.col_name}'}}"


class SelectionType(Enum):
    single_value = "single_value"
    numeric_range = "numeric_range"
    string_set = "string_set"
    empty = "empty"


class SelectionValue(object):
    """
    column [ColumnRed]
    selection_type [SelectionType]
    """
    column: ColumnRef
    selection_type: SelectionType
    def __init__(self):
        raise InternalLogicalError("SelectionValue is abstract and should not be instantiated")

    def to_str(self):
        raise InternalLogicalError("SelectionValue is abstract and should not be instantiated")


class EmptySelection(SelectionValue):
    def __init__(self, column: ColumnRef):
        self.column = column
        self.selection_type = SelectionType.empty

    def __eq__(self, other: SelectionValue):
        if other.selection_type != SelectionType.empty:
            return False
        if self.column != other.column:
            return False
        return True

    def to_str(self):
        raise InternalLogicalError("Should not try to make empty selections into strings")

    def __repr__(self):
        return f"{{column: {self.column}, val: None, minVal: None, maxVal: None}}"


class NumericRangeSelection(SelectionValue):
    def __init__(self, column: ColumnRef, minVal: float, maxVal: float):
        self.selection_type = SelectionType.numeric_range
        self.column = column
        self.minVal = minVal
        self.maxVal = maxVal

    def __eq__(self, other: SelectionValue):
        if other.selection_type != SelectionType.numeric_range:
            return False
        m_other = cast(NumericRangeSelection, other)
        if self.column != m_other.column:
            return False
        if self.minVal != m_other.minVal:
            return False
        if self.maxVal != m_other.maxVal:
            return False
        return True

    def __repr__(self):
        return f"{{column: {self.column}, minVal: {self.minVal}, maxVal: {self.maxVal}}}"

    def __str__(self) -> str:
        return self.__repr__()

    def to_str(self):
        return f'{{"{self.column.df_name}": {{"{self.column.col_name}": [{self.minVal}, {self.maxVal}]}}}}'



class SetSelection(SelectionValue):
    def __init__(self, column: ColumnRef, val: Set):
        self.selection_type = SelectionType.string_set
        self.column = column
        self.val = val

    def __eq__(self, other: SelectionValue):
        if other.selection_type != SelectionType.string_set:
            return False
        if self.column != other.column:
            return False

        s_other = cast(SetSelection, other)
        # python has convenient set operations...
        if self.val != s_other.val:
            return False
        return True

    def __repr__(self):
        return f"{{column: {self.column}, val: {self.val}}}"

    def __str__(self) -> str:
        return self.__repr__()

    def to_str(self):
        return f'{{"{self.column.df_name}": {{"{self.column.col_name}": {json.dumps(self.val)}}}}}'
