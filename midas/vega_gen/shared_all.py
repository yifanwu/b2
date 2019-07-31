from .defaults import CHART_HEIGHT, CHART_WIDTH


def gen_spec_base():
    return {
            "$schema": "https://vega.github.io/schema/vega/v5.json",
            "width": CHART_WIDTH,
            "height": CHART_HEIGHT,
            "padding": 5,
        }
