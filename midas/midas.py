from __future__ import absolute_import

from . import utils
import json
import uuid
import copy

from IPython.display import display, publish_display_data

from .utils import prepare_spec

class Midas(object):
    """Create Interactive visualization in the Jupyter Notebook"""
    
    def __init__(self, spec, data=None, opt=None):
        """Initialize the visualization object."""
        spec = spec
        self.opt = opt or {}
        self.spec = self._prepare_spec(spec, data)

    def _prepare_spec(self, spec, data):
        return prepare_spec(spec, data)

    def _generate_js(self, id, **kwds):
        template = utils.get_content("static/vega.js")
        payload = template.format(
            id=id,
            spec=json.dumps(self.spec, **kwds),
            opt=json.dumps(self.opt, **kwds),
            # type=self.render_type
            # support vega only for now, since
            # - internal use
            # - better signal handling support
            type="vega"
        )
        return payload

    def _repr_mimebundle_(self, include=None, exclude=None):
        """Display the visualization in the Jupyter notebook."""
        id = uuid.uuid4()
        return (
            {'application/javascript': self._generate_js(id)},
            {'midas': '#{0}'.format(id)},
        )

    def display(self):
        """Render the visualization."""
        display(self)


# not sure wha the following is doing...
# def entry_point_renderer(spec, embed_options=None):
#     vl = Midas(spec, opt=embed_options)
#     vl.display()
#     return {'text/plain': ''}


__all__ = ['Midas']
# , 'entry_point_renderer']
