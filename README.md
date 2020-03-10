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

## Hard Coding Note

There is instrumentation for experimentation currently that is hard coded to Yifan's dev path: `midas/constants.py`:

```python
LOG_DB_PATH = "/Users/yifanwu/dev/midas-experiment/experiment_results/experiment_log.sqlite"
LOG_DB_BACKUP_FOLDER = "/Users/yifanwu/dev/midas-experiment/experiment_results/backups/"
```

You should be sure not to invoke midas with `Midas("somestring")`, or to create the relevant sqlite files and folders.