# Midas, Fast Custom Visualization Interaction in Notebooks

## Installation Guide

```bash
git submodule init
git submodule update
```

To follow the example notebooks, note that you should add the following to your IPython config file (as it expects the extension to be auto-loaded)

```python
c.InteractiveShellApp.extensions = [
    'midas'
]
```

## Development Guide

Install requirements: `pip install -r requirements.txt`

Symlink files instead of copying files:

```sh
python setup.py develop
yarn install
npm run build # yarn watch if in dev mode for continuous update
jupyter nbextension install --py --symlink midas  # not needed in notebook >= 5.3
```

You will need to understand how [git submodules](https://git-scm.com/book/en/v2/Git-Tools-Submodules) work.

To test the Python pieces: `pytest -q ./tests/test_rendering.py`.

Publish a new version to pypi with `python3 setup.py sdist upload`.
