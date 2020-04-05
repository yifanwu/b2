import random
import string
import codecs
from os import path
import traceback
import ast
import sqlite3
from re import sub
import requests
from pathlib import Path
import time 
from datetime import datetime

from typing import Tuple, List, Optional
from IPython import get_ipython  # type: ignore
from IPython.core.debugger import set_trace

from midas.constants import ISDEBUG
from midas.util.errors import UserError, InternalLogicalError

FG_BLUE = "\x1b[34m";
RESET_PRINT = "\x1b[0m";

def fetch_and_cache(data_url, file, data_dir="data", force=False):
    """
    Download and cache a url and return the file object.
    
    data_url: the web address to download
    file: the file in which to save the results.
    data_dir: (default="data") the location to save the data
    force: if true the file is always re-downloaded 
    
    return: The pathlib.Path object representing the file.
    """
    
    data_dir = Path(data_dir)
    data_dir.mkdir(exist_ok = True)
    file_path = data_dir / Path(file)
    # If the file already exists and we want to force a download then
    # delete the file first so that the creation date is correct.
    if force and file_path.exists():
        file_path.unlink()
    if force or not file_path.exists():
        print('Downloading...', end=' ')
        resp = requests.get(data_url)
        with file_path.open('wb') as f:
            f.write(resp.content)
        print('Done!')
        last_modified_time = time.ctime(file_path.stat().st_mtime)
    else:
        last_modified_time = time.ctime(file_path.stat().st_mtime)
        print("Using cached version that was downloaded (UTC):", last_modified_time)
    return file_path
    

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

def get_log_entry_fun(user_id: str, task_id: str):
    start_time = datetime.now()
    time_stamp = start_time.strftime("%Y%m%d-%H%M%S")
    log_entry_to_db = open_sqlite_for_logging(user_id, task_id, time_stamp)
    def log_entry(fun_name: str, optional_metadata: Optional[str]=None):
        call_time = datetime.now()
        diff = (call_time - start_time).total_seconds()
        meta = optional_metadata if optional_metadata else ''
        log_entry_to_db(fun_name, diff, meta)
    return log_entry 

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


def _get_first_target_from_prev_line(stack):
    try:
        prev_line = stack[-3]
        code = prev_line.splitlines()[1]
        body = ast.parse(code.strip()).body[0]
        first_target = body.targets[0] # type: ignore
        return first_target
    except:
        return None


def find_tuple_name():
    try:
        stack = traceback.format_stack()
        first_target = _get_first_target_from_prev_line(stack)
        a = first_target.elts[0].id # type: ignore
        b = first_target.elts[1].id # type: ignore
        return a, b
    except:
        return None
    
        
def find_name(throw_error=False):
    try:
        stack = traceback.format_stack()
        first_target = _get_first_target_from_prev_line(stack)
        a = first_target.id # type: ignore
        if throw_error and (a is None):
            raise InternalLogicalError("We did not get a name when expected!")
        return a
    except:
        if throw_error:
            raise UserError("We expect you to assign this compute to a variable")
        return None


ifnone = lambda a, b: b if a is None else a


def get_min_max_tuple_from_list(values: List[float]) -> Tuple[float, float]:
    """sets in place the array if the values are not min and max
    
    Arguments:
        x_value {List[int]} -- [description]
    
    Returns:
       returns the modifed array in place
    """
    return (min(values), max(values))
