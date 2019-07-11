
class Midas(object):
    """Create Interactive visualization in the Jupyter Notebook"""

    def _prepare_spec(self, spec, data):
        return prepare_spec(spec, data)

def entry_point_renderer(spec, embed_options=None):
    vl = Midas(spec, opt=embed_options)
    vl.display()
    return {'text/plain': ''}


__all__ = ['Midas', 'entry_point_renderer']
