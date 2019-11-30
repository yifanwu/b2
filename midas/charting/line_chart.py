from midas.vis_types import EncodingSpec
from midas.constants import IS_OVERVIEW_FIELD_NAME

def gen_linechart_spec(encoding: EncodingSpec, df_name: str):
    spec = {
        "$schema": "https://vega.github.io/schema/vega-lite/v4.json",
        "description": df_name,
        "data": { "values": [] },
        "mark": "line",
        "encoding": {
            "x": {"field": encoding.x, "type": "temporal"},
            "y": {"field": encoding.y, "type": "quantitative"}
        },
        "color": {
            "field": IS_OVERVIEW_FIELD_NAME, "type": "nominal",
            "scale": {"range": ["gray", "blue"]}
        },
        "opacity": {"value": 0.7}
    }
    return spec