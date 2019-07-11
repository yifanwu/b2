# Midas, Fast Custom Visualization Interaction in Notebooks

Modeled after [ipyvega](https://github.com/vega/ipyvega).


## Developers

Install requirements: `pip install -r requirements.txt`

Symlink files instead of copying files:

```sh
python setup.py develop
jupyter nbextension install --py --symlink midas  # not needed in notebook >= 5.3
```

Run kernel: `jupyter notebook`

To rebuild the javascript continuously, run `yarn watch`.

Publish a new version to pypi with `python3 setup.py sdist upload`.
