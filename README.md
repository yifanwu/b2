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
jupyter nbextension install --py --symlink midas
```

You will need to understand how [git submodules](https://git-scm.com/book/en/v2/Git-Tools-Submodules) work.

To test the Python pieces: `pytest -q ./tests/test_rendering.py`.

Publish a new version to pypi with `python3 setup.py sdist upload`.

It is also recommended that you install PyRight if you are using the VSCode editor, or PyCharm, which should come with type checking.

When you change the JS code, you have to run `npm run watch` for the TypeScript to build and then you also have to refresh the notebook that you have open.

When you change the Python side code, you can use the following at the beginning of your notebook, and you might need to rerun the cells that load in the library (and cells that depend on it)---you might also need to restart the kernel if that does not work.

```python
%load_ext autoreload
%autoreload 2
```
