import random
import string
import codecs
from midas.midas_algebra.selection import ColumnRef, EmptySelection, SelectionValue
from midas.util.errors import UserError, InternalLogicalError
from os import path
import traceback
import ast

from typing import Tuple, List, Optional
from IPython import get_ipython  # type: ignore


def isnotebook():
    try:
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':
            return True   # Jupyter notebook or qtconsole
        elif shell == 'TerminalInteractiveShell':
            return False  # Terminal running IPython
        else:
            return False  # Other type (?)
    except NameError:
        return False      # Probably standard Python interpreter


def abs_path(p: str):
    """Make path absolute."""
    return path.join(path.dirname(path.abspath(__file__)), p)


def check_path(p: str):
    if not path.exists(p):
        raise UserWarning(f"The path you provided, {p} does not exists")


def get_content(path):
    """Get content of file."""
    with codecs.open(abs_path(path), encoding='utf-8') as f:
        return f.read()


def get_random_string(stringLength=10):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))


def find_name(throw_error=False) -> Optional[str]:
    prev_line = traceback.format_stack()[-3]
    code = prev_line.splitlines()[1]
    body = ast.parse(code.strip()).body[0]
    if hasattr(body, 'targets'):
        a = body.targets[0].id # type: ignore
        if throw_error and (a is None):
            raise InternalLogicalError("We did not get a name when expected!")
        # debug_log(f"found name {a}")
        return a
    elif throw_error:
        raise UserError("We expect you to assing this compute to a variable")
    # debug_log("find_name did NOT find a name")
    return None

ifnone = lambda a, b: b if a is None else a


def diff_selection_value(new_selection: List[SelectionValue], old_selection: List[SelectionValue])-> List[SelectionValue]:
    """returns the difference between the values
    Arguments:
        new_selection {List[SelectionValue]} -- one selection
        old_selection {List[SelectionValue]} -- another selection
    Returns:
        returns
        - None if there are no changes
        - an empty selection if the selection is removed
        - all the new diffs as selections
    """
    def find_selection(a_selection: SelectionValue, selections: List[SelectionValue]):
        for s in selections:
            if s == a_selection:
                return True
        return False

    def find_df(df: ColumnRef, selections: List[SelectionValue]):
        for s in selections:
            if s.column == df:
                return True
        return False

    diff = []
    # iterate through the items in new_selection
    for s in new_selection:
        if not find_selection(s, old_selection):
            diff.append(s)
    for s in old_selection:
        if not find_df(s.column, new_selection):
            # this means that this item has been removed
            diff.append(EmptySelection(s.column))
    return diff

def get_min_max_tuple_from_list(values: List[float]) -> Tuple[float, float]:
    """sets in place the array if the values are not min and max
    
    Arguments:
        x_value {List[int]} -- [description]
    
    Returns:
       returns the modifed array in place
    """
    return (min(values), max(values))
    