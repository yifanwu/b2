# Midas, Fast Custom Visualization Interaction in Notebooks

## Installation Guide

To follow the example notebooks, note that you should add the followign to your Ipython config file (as it expects the extension to be autoloaded)

```python
c.InteractiveShellApp.extensions = [
    'midas'
]
```


## Developement Guide

Install requirements: `pip install -r requirements.txt`

Symlink files instead of copying files:

```sh
python setup.py develop
yarn build # yarn watch if in dev mode for continuous update
jupyter nbextension install --py --symlink midas  # not needed in notebook >= 5.3
```

To test the Python pieces: `pytest -q ./tests/test_rendering.py`.

Publish a new version to pypi with `python3 setup.py sdist upload`.
