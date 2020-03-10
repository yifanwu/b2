# Midas, Reifying Interactions in Jupyter Notebook

## 🚧 Warning 🚧

The code is still under heavy construction; please check back on status.

## Installation Guide

Clone the repository and cd into the project:

```sh
npm run install
npm run build
python setup.py develop
jupyter nbextension install --py --symlink midas
```

Note the JS file has been built and deployed at `midas/static/index.js`.