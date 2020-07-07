from __future__ import absolute_import
from warnings import warn

from .b2 import B2
from .algebra.dataframe import MidasDataFrame

__all__ = ['B2', 'MidasDataFrame']

__version__ = '0.0.5'


def _jupyter_nbextension_paths():
    """Return metadata for the nbextension."""
    return [dict(
        section="notebook",
        # the path is relative to the `midas` directory
        src="static",
        # directory in the `nbextension/` namespace
        dest="b2",
        # _also_ in the `nbextension/` namespace
        require="b2/index")]


def find_static_assets():
    warn("""To use the nbextension, you'll need to update
    the Jupyter notebook to version 4.2 or later.""")
    return []
