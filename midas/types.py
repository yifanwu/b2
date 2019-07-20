from enum import Enum
from typing import NamedTuple
from datetime import datetime


class DfMetaData(NamedTuple):
    time_created: datetime

class ChartType(Enum):
    bar = "bar"
    scatter = "scatter"
    line = "line"

