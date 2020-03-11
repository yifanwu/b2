import random
import string
import codecs
from os import path
import traceback
import ast
import sqlite3
from datetime import datetime
from shutil import copyfile, copy
from re import sub

from typing import Tuple, List, Optional
from IPython import get_ipython  # type: ignore
from IPython.core.debugger import set_trace

from midas.constants import ISDEBUG
from midas.midas_algebra.selection import ColumnRef, EmptySelection, SelectionValue
from midas.util.errors import UserError, InternalLogicalError


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


def red_print(m):
    print(f"\x1b[31m{m}\x1b[0m")

LOG_SQL_SETUP_LOG = """
CREATE TABLE log (
  session_id  TEXT,
  action      TEXT,
  seconds_since_start INTEGER,
  optional_metadata   TEXT
);
"""

LOG_SQL_SETUP_SESSION = """
CREATE TABLE session (
  user_id    TEXT,
  task_id    TEXT,
  session_id TEXT,
  start_time TEXT
);
"""


def open_sqlite_for_logging(user_id: str, task_id: str, time_stamp: str):
    """opens sqlite file for experuiment logging purpose
    
    Note that this is not associated with Midas operations.
    
    Arguments:
        user_id {str} -- the id assigned to the experiment participant
        time_stamp {[type]} -- [description]
    
    Returns:
        [type] -- [description]
    """
    session_id = f'{user_id}_{task_id}_{time_stamp}'
    # copy(LOG_DB_PATH, f'{LOG_DB_BACKUP_FOLDER}{session_id}.sqlite')
    file_name = f"./experiment_log_{user_id}.sqlite"
    should_execute_setup = not path.exists(file_name)
    # check if it's there
    # if not, do the initial setup
    con = sqlite3.connect(file_name)
    cur = con.cursor()

    if should_execute_setup:
        cur.execute(LOG_SQL_SETUP_LOG)
        cur.execute(LOG_SQL_SETUP_SESSION)
        con.commit()

    cur.execute(f"INSERT INTO session VALUES ('{user_id}', '{task_id}', '{session_id}', '{time_stamp}')")
    con.commit()

    def log_entry_to_db(fun_name: str, diff: float, optional_metadata: str):
        sql = f"INSERT INTO log VALUES ('{session_id}', '{fun_name}', {diff}, '{optional_metadata}');"
        try:
            cur.execute(sql)
            con.commit()
        # @type: ignore
        except sqlite3.OperationalError as error:
            red_print(f"Tried to execute {sql}, but got {error}")

    return log_entry_to_db


def abs_path(p: str):
    """Make path absolute."""
    return path.join(path.dirname(path.abspath(__file__)), p)


def check_path(p: str):
    if not path.exists(p):
        raise UserWarning(f"The path you provided, {p} does not exists")


def sanitize_string_for_var_name(p: str):
    return sub('[^0-9a-zA-Z]+', '_', p)




def get_content(path):
    """Get content of file."""
    with codecs.open(abs_path(path), encoding='utf-8') as f:
        return f.read()


def get_random_string(stringLength=10):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))


def find_name(throw_error=False) -> Optional[str]:
    try:
        # if ISDEBUG: set_trace()
        prev_line = traceback.format_stack()[-3]
        code = prev_line.splitlines()[1]
        body = ast.parse(code.strip()).body[0]
        if hasattr(body, 'targets'):
            a = body.targets[0].id # type: ignore
            if throw_error and (a is None):
                raise InternalLogicalError("We did not get a name when expected!")
            return a
        elif throw_error:
            raise UserError("We expect you to assign this compute to a variable")
        return None
    except:
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

def find_selections_with_df_name(current_selection: List[SelectionValue], df_name):
    r = []
    for s in current_selection:
        if s.column.df_name == df_name:
            r.append(s.column)
    return r
