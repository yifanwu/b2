# Midas, Fast Custom Visualization Interaction in Notebooks

Modeled after [ipyvega](https://github.com/vega/ipyvega).

## Developers

Install requirements: `pip install -r requirements.txt`

Symlink files instead of copying files:

```sh
python setup.py develop
yarn build # yarn watch if in dev mode for continuous update
jupyter nbextension install --py --symlink midas  # not needed in notebook >= 5.3
```

To test the Python pieces: `pytest -q ./tests/test_rendering.py`.

Publish a new version to pypi with `python3 setup.py sdist upload`.
