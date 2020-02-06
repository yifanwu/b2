class MidasConfig(object):
    def __init__(self, linked: bool, logging: bool):
        self.linked = linked
        self.logging = logging

# default_midas_config = MidasConfig(True, True)

IS_DEBUG = True
# IS_DEBUG = False