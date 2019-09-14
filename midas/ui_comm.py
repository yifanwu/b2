from ipykernel.comm import Comm

from .constants import MIDAS_CELL_COMM_NAME

class UiComm(object):
    midas_cell_comm: Comm
    def __init__(self):
        self.nextId = 0
        self.midas_cell_comm = Comm(target_name=MIDAS_CELL_COMM_NAME)
