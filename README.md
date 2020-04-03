# Midas

Midas is a Jupyter extension that augments your programming experience with interactive visualizations for data analysis.

**Load dataframes to visualizations in a dashboard area that you can interact with**

![demo image](https://github.com/yifanwu/midas-exp-pub/blob/master/figs/demo.png?raw=true)

**Using interactions to drive cell computation using _reactive cells_**

![reactive demo](https://github.com/yifanwu/midas-exp-pub/blob/master/figs/reactive_demo.png?raw=true)

And more!  See [here](https://github.com/yifanwu/midas-exp-pub) for tutorials.

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
# or `npm run build`
npm run watch
```

## People

Midas is developed by [Yifan](http://yifanwu.net/) at UC Berkeley, with advising from [Joe](https://www2.eecs.berkeley.edu/Faculty/Homepages/hellerstein.html), [Arvind](https://arvindsatya.com/), and others.

If you are interested in using Midas or participating in our user study, please send Yifan a message at yifanwu@berkeley.edu.
