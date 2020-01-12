# Midas, Reifying Interactions in Jupyter Notebook

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
