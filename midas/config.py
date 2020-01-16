class MidasConfig(object):
    def __init__(self, linked: bool):
        self.linked = linked

default_midas_config = MidasConfig(True)

IS_DEBUG = True
# IS_DEBUG = False