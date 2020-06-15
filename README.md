# Midas

Midas is a Jupyter extension that augments your programming experience with interactive visualizations for data analysis.

**Load dataframes to visualizations in a dashboard area that you can interact with**

<img src="https://github.com/yifanwu/midas-exp-pub/blob/master/figs/demo.png?raw=true" width="600px">

**Using interactions to drive cell computation using _reactive cells_**

<img src="https://github.com/yifanwu/midas-exp-pub/blob/master/figs/reactive_demo.png" width="600px">

And more---see [here](https://github.com/yifanwu/midas-exp-pub) for tutorials. If you ran into problems, feel free to [open an issue](https://github.com/yifanwu/midas/issues/new/choose), or email Yifan directly at yifanwu@berkeley.edu, or [via Twitter](https://twitter.com/yifanwu). We are also actively recruiting participants for a user study, if you might be interested, please fill out [this form](https://forms.gle/gEjNh7juBkQN3EZA6).

## Installation

```sh
pip install midas-ext
```

## Development

To build your own JS bundle:

```sh
pip install -r requirements.txt
python setup.py develop
jupyter nbextension install --py --symlink midas
```

```sh
npm run install
npm run watch
```

## Deployment

```sh
npm run build
python setup.py sdist
twine upload dist/*
```

You may need `pip install twine` if you do not have `twine` already; as well as a PyPi account and permissions.

## People

Midas is developed by [Yifan](http://yifanwu.net/) at UC Berkeley, with advising from [Joe](https://www2.eecs.berkeley.edu/Faculty/Homepages/hellerstein.html), [Arvind](https://arvindsatya.com/), and others.

If you are interested in using Midas or participating in our user study, please send Yifan a message at yifanwu@berkeley.edu.
