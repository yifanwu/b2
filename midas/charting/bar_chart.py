from midas.vis_types import EncodingSpec
from midas.constants import IS_OVERVIEW_FIELD_NAME

# the seletion signalis "brush", which, for example, looks like `{"a":["A","C","E","G"]}`
def gen_bar_chart_spec(encoding: EncodingSpec, df_name: str):
    spec = {
        "$schema": "https://vega.github.io/schema/vega-lite/v4.json",
        "description": f"Midas Generated Visualization of dataframe {df_name}",
        "selection": {
            "brush": {
                "type": "interval",
                "encodings": ["x"]
            }
        },
        "data": {
            "values": []
        },
        "mark": "bar",
        "encoding": {
            "x": {
                "field": encoding.x,
                "type": "ordinal"
            },
            "y": {
                "field": encoding.y,
                "type": "quantitative",
                "stack": None
            },
            "color": {
                "field": IS_OVERVIEW_FIELD_NAME, "type": "nominal",
                "scale": {"range": ["gray", "blue"]}
            },
            "opacity": {"value": 0.7}
        }
    }
    return spec

