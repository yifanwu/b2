from __future__ import print_function
import json
from pandas import DataFrame
from typing import List, Optional, Dict

from .errors import debug_log
from .vega_gen.defaults import DEFAULT_DATA_SOURCE
from .utils import dataframe_to_dict
from .widget_types import UpdateDataMessage, SignalMessage, WidgetMessageType

try:
    from ipywidgets import DOMWidget
    from traitlets import Unicode
except ImportError as err:
    new_err = ImportError(
        "midas.widget requires ipywidgets, which could not be imported. "
        "Is ipywidgets installed?"
    )

    # perform manual exception chaining for python 2 compat
    new_err.__cause__ = err
    raise new_err


__all__ = ['MidasWidget']


class MidasWidget(DOMWidget):
    _view_name = Unicode('MidasWidget').tag(sync=True)
    _view_module = Unicode('nbextensions/midas/widget').tag(sync=True)
    _view_module_version = Unicode('0.0.1').tag(sync=True)
    _spec_source = Unicode('null').tag(sync=True)
    _opt_source = Unicode('null').tag(sync=True)
    
    def __init__(self, title:str, spec=None, opt=None, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self._spec_source = json.dumps(spec)
        self._opt_source = json.dumps(opt)
        self._has_waited = False

        self._displayed = False
        self._pending_signal_message: List[Dict] = []
        self._pending_data_updates: List[Dict] = []

        self.on_msg(self._handle_message)


    def _handle_message(self, widget, msg, _):
        if msg['type'] != "display":
            return

        if self._displayed:
            return

        self._displayed = True

        if self._pending_data_updates:
            self.send(dict(
                type = WidgetMessageType.update_data.value,
                updates = self._pending_data_updates
            ))
            self._pending_data_updates = []
            
        if self._pending_signal_message:
            self.send(dict(
                type = WidgetMessageType.register_signal_callback.value,
                callbacks = self._pending_signal_message
            ))
            self._pending_signal_message = []
        return

        
    def _reset(self):
        self._displayed = False
        self._pending_data_updates = []

    @property
    def spec(self):
        return json.loads(self._spec_source)

    @spec.setter
    def spec(self, value):
        self._spec_source = json.dumps(value)
        self._reset()

    @property
    def opt(self):
        return json.loads(self._opt_source)


    @opt.setter
    def opt(self, value):
        self._opt_source = json.dumps(value)
        self._reset()


    # the new data is a dataframe
    def replace_data(self, new_df: DataFrame, key=DEFAULT_DATA_SOURCE):
        """Replaces the chart data
        works by creating a remove function that removes everything
        """
        new_values = dataframe_to_dict(new_df)
        insert = new_values
        remove = 'true'
        update = dict(key=key, insert=insert, remove=remove)
        debug_log(f"\nNew dataframe\n{new_values}\n")
        if self._displayed:
            self.send(dict(
                type=WidgetMessageType.update_data.value,
                updates=[update]
            ))
        else:
            self._pending_data_updates.append(update)


    def register_signal_callback(self, signal: str, callback: str):
        """register_signal_callback attaches the JS based callback
            assuming that it takes the varialbes "name", and "value", based on the vega spec
        
        Arguments:
            signal {str} -- [description]
            callback {str} -- [description]
        """
        # debug_log(f"registered callback for signal {signal}: {callback}")
        cb = dict(signal=signal, callback=callback)
        if self._displayed:
            self.send(dict(
                type=WidgetMessageType.register_signal_callback.value,
                callbacks=[cb]
            ))
        else:
            self._pending_signal_message.append(cb)


