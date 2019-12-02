from datetime import datetime
from typing import Dict, List

from .midas_algebra.dataframe import MidasDataFrame, DFInfo, VisualizedDFInfo
from .util.errors import InternalLogicalError, debug_log, type_check_with_warning
from .vis_types import SelectionEvent
from .state_types import DFName
from .ui_comm import UiComm


class State(object):
    # FIXME: we might want to support a history of MidasDataFrames! as opposed to an update in place for dfinfo
    # series: Dict[str, Ser]
    nextId: int

    def __init__(self, uiComm: UiComm):
        self.groupbys = {}
        self.ui_comm = uiComm
        self.shelf_selections = {}

