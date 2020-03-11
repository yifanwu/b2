# Midas: Moving Between Code and Interactive Visualizations 🚧

The code is still under heavy construction.

## Installation Guide

We assume that you have Jupyter Notebook (_not Lab_) installed already.  Clone the repository and cd into the project's root directory:

```sh
pip install -r requirements.txt
python setup.py develop
jupyter nbextension install --py --symlink midas
```

Note the JS file has been built and deployed at `midas/static/index.js`.

## Dev Installation Guide

To build your own JS bundle:

```sh
npm run install
npm run watch
```

Alternatively you can do `npm run build` instead of watch. The rest is the same.
