from midas.constants import IS_OVERVIEW_FIELD_NAME
# I think vega-lite is simple enough that we might just be able to not bother reusing code here

# the seletion signalis "brush", which, for example, looks like `{"a":["A","C","E","G"]}`
def gen_bar_chart_spec(x_field: str, y_field: str, df_name: str):
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
                "field": x_field,
                "type": "ordinal"
            },
            "y": {
                "field": y_field,
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

