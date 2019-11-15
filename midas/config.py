DEBOUNCE_RATE_MS = 200
CUSTOM_FUNC_PREFIX = "__m_"
MIDAS_INSTANCE_NAME = "m"


class MidasConfig(object):
    def __init__(self, linked: bool):
        self.linked = linked

default_midas_config = MidasConfig(True)