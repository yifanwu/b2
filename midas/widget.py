from __future__ import print_function
import json


from .vega_gen.defaults import DEFAULT_DATA_SOURCE


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

    def __init__(self, spec=None, opt=None, **kwargs):
        super().__init__(**kwargs)
        self._spec_source = json.dumps(spec)
        self._opt_source = json.dumps(opt)

        self._displayed = False
        self._pending_updates = []

        self.on_msg(self._handle_message)

    def _handle_message(self, widget, msg, _):
        if msg['type'] != "display":
            return

        if self._displayed:
            return

        self._displayed = True

        if not self._pending_updates:
            return

        self.send(dict(type="update", updates=self._pending_updates))
        self._pending_updates = []

    def _reset(self):
        self._displayed = False
        self._pending_updates = []

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


    def update(self, key, remove=None, insert=None):
        """Update the chart data.

        Updates are only reflected on the client, i.e., after re-displaying
        the widget will show the chart specified in its spec property.

        :param Optional[str] remove:
            a JavaScript expression of items to remove. The item to test can
            be accessed as ``datum``. For example, the call
            ``update(remove="datum.t < 5")`` removes all items with the
            property ``t < 5``.

        :param Optional[List[dict]] insert:
            new items to add to the chat data.
        """
        update = dict(key=key)

        if remove is not None:
            update['remove'] = remove

        if insert is not None:
            update['insert'] = insert

        if self._displayed:
            self.send(dict(type="update", updates=[update]))

        else:
            self._pending_updates.append(update)


    # the new data is a dataframe
    def replace_data(self, newDf, key=DEFAULT_DATA_SOURCE):
        """Replaces the chart data
        works by creating a remove function that removes everything
        """
        newValues = newDf.to_dict('records')
        self.update(key, insert=newValues, remove='true')


    def register_signal_callback(self, signal: str, callback: str):
        """register_signal_callback attaches the JS based callback
            assuming that it takes the varialbes "name", and "value", based on the vega spec
        
        Arguments:
            signal {str} -- [description]
            callback {str} -- [description]
        """
        # print(f"registered callback for signal {signal}: {callback}")
        registerSignal = dict(signal=signal, callback=callback)
        # FIXME: probably nee dot check 
        self.send(dict(type="registerSignal", callbacks=[registerSignal]))


