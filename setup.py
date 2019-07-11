LONG_DESCRIPTION = """
Midas
============

IPython/Jupyter notebook module that enables developers to get visualizations from dataframes with simple specifications

Using `Vega <https://github.com/vega/vega/>` and `Vega-Lite <https://github.com/vega/vega-lite/>`.

For more information, see https://github.com/yifanwu/midas.
"""

DESCRIPTION         = "Midas: An IPython/Jupyter widget for interacting with dataframes"
NAME                = "midas"
PACKAGES            = ['midas',
                       'midas.tests']
PACKAGE_DATA        = {'midas': ['static/*.js',
                                'static/*.js.map',
                                'static/*.html']}
AUTHOR              = 'Yifan Wu'
AUTHOR_EMAIL        = 'yifanwu@berkeley.edu'
URL                 = 'http://github.com/yifanwu/midas'
DOWNLOAD_URL        = 'http://github.com/yifanwu/midas'
LICENSE             = 'BSD 3-clause'
DATA_FILES          = [
                            ('share/jupyter/nbextensions/midas', [
                             'midas/static/index.js',
                             'midas/static/index.js.map',
                             'midas/static/widget.js',
                             'midas/static/widget.js.map',
                            ]),
                            ('etc/jupyter/nbconfig/notebook.d' , ['midas.json'])
                        ]
ENTRY_POINTS        = {'altair.vegalite.v3.renderer': ['notebook=midas:entry_point_renderer']}
EXTRAS_REQUIRE      = {'widget': ['ipywidgets']}


import io
import os
import re

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


def read(path, encoding='utf-8'):
    path = os.path.join(os.path.dirname(__file__), path)
    with io.open(path, encoding=encoding) as fp:
        return fp.read()


def version(path):
    """Obtain the packge version from a python file e.g. pkg/__init__.py

    See <https://packaging.python.org/en/latest/single_source_version.html>.
    """
    version_file = read(path)
    version_match = re.search(r"""^__version__ = ['"]([^'"]*)['"]""",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


VERSION = version('midas/__init__.py')


setup(name=NAME,
      version=VERSION,
      description=DESCRIPTION,
      long_description=LONG_DESCRIPTION,
      author=AUTHOR,
      author_email=AUTHOR_EMAIL,
      url=URL,
      download_url=DOWNLOAD_URL,
      license=LICENSE,
      packages=PACKAGES,
      package_data=PACKAGE_DATA,
      data_files=DATA_FILES,
      entry_points=ENTRY_POINTS,
      extras_require=EXTRAS_REQUIRE,
      include_package_data=True,
      classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6'],
     )
