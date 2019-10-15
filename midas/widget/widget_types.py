from enum import Enum
from typing import NamedTuple, Optional, List, Union

class WidgetMessageType(Enum):
    update_data = "update"
    register_signal_callback = "registerSignal"

class SignalMessage(NamedTuple):
    signal: str
    callback: str


class UpdateDataMessage(NamedTuple):
    insert: List[dict]
    remove: str


class WidgetMessage(NamedTuple):
    message_type: WidgetMessageType
    message: Union[SignalMessage, UpdateDataMessage]
    
