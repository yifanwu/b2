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
import numpy as np
from datetime import datetime

from typing import Tuple, List, Optional
from IPython import get_ipython  # type: ignore
from IPython.core.debugger import set_trace

from midas.constants import ISDEBUG
from midas.util.errors import UserError, InternalLogicalError
from datascience import are

FG_BLUE = "\x1b[34m";
RESET_PRINT = "\x1b[0m";
FG_PURPLE = "\x1b[035m"

def plot(v, center, zoom_start, radius):
    import folium
    import folium.plugins
    locs = v.to_numpy()
    us_map = folium.Map(location=center, zoom_start = zoom_start)
    heatmap = folium.plugins.HeatMap(locs.tolist(), radius = radius)
    us_map.add_child(heatmap)
    return us_map

def plot_heatmap(locs_df, zoom_start=12, radius=12):
    """Plots a heatmap using the Folium library
    
    Arguments:
        locs_df {MidasDatabFrame} -- Should contain lat, lon (in that order)
    
    Keyword Arguments:
        zoom_start {int} -- the higher the value, the more zoomed out (default: {12})
        radius {int} -- how to aggregate the heatmap (default: {12})
    """
    # basic data cleaning
    # compute the center
    center_lat = np.average(locs_df[locs_df.labels[0]])
    center_lon = np.average(locs_df[locs_df.labels[1]])
    if np.isnan(center_lat):
        filtered = locs_df.where(locs_df.labels[0], lambda x: not np.isnan(x))
        diff_len = len(locs_df) - len(filtered)
        center_lat = np.average(filtered[filtered.labels[0]])
        center_lon = np.average(filtered[filtered.labels[1]])
        print(f"{FG_PURPLE}[Notification] Filtered out {diff_len} NaN values.{RESET_PRINT}")
        return plot(filtered, [center_lat, center_lon], zoom_start, radius)
    else:
        return plot(locs_df, [center_lat, center_lon], zoom_start, radius)




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
