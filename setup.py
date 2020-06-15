LONG_DESCRIPTION = """
Midas
============

Reification of interactions in Jupyter Notebook.

For more information, see https://github.com/yifanwu/midas.
"""

DESCRIPTION         = "Midas: Reification of interactions in Jupyter Notebook"
NAME                = "midas-ext"
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
                             'midas/static/index.js.map'
                            ]),
                            ('etc/jupyter/nbconfig/notebook.d' , ['midas.json'])
                        ]
# EXTRAS_REQUIRE      = {'foldcode': ['codemirror/addon/fold/foldcode']}


import io
import os
import re

try:
    from setuptools import setup, find_packages
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
      packages=find_packages(),
      package_data=PACKAGE_DATA,
      data_files=DATA_FILES,
    #   extras_require=EXTRAS_REQUIRE,
      include_package_data=True,
      classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Other Environment',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7'],
     )
