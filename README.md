# Midas

Midas is a Jupyter extension that augments your programming experience with interactive visualizations for data analysis. You can find a basic tutorial [here](https://github.com/yifanwu/midas-exp-pub/blob/master/MidasTutorial.ipynb) (note that you must open it locally after installation).

🚧The code is still under heavy construction---please know that the UX and API are both subject to change. There are a few bugs here and there which we are working on fixing.🚧

## Installation Guide

We assume that you have Jupyter Notebook installed already, running in Python 3.  Clone the repository and cd into the project's root directory:

```sh
pip install -r requirements.txt
python setup.py develop
jupyter nbextension install --py --symlink midas
```

Note the JS file has been built and deployed at `midas/static/index.js`. We are looking into making it accessible by `pip`. Stay tuned.

## Dev Installation Guide

To build your own JS bundle:

```sh
npm run install
npm run watch
```

Alternatively you can do `npm run build` instead of watch. The rest is the same.

## People

Midas is developed by [Yifan](http://yifanwu.net/) at UC Berkeley, with advising from [Joe](https://www2.eecs.berkeley.edu/Faculty/Homepages/hellerstein.html), [Arvind](https://arvindsatya.com/), and others.

If you are interested in using Midas or participating in our user study, please send Yifan a message at yifanwu@berkeley.edu.
