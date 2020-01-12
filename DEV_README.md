# Development Guide

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

In addition, know that if the JavaScript side triggers any computation in Python, the print messages will not surface---if you want to do better testing, you can use the `comm` to send a debug message (in place of printing) for the entry call, and then you can mock the input by running code, which behaves like normal executions and prints normally.


## Code Notes

Code with `#REDZONE` are places where it is brittle and assumptions might be broken.
