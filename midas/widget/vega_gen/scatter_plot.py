from midas.constants import IS_OVERVIEW_FIELD_NAME

def gen_scatterplot_spec(x_field: str, y_field: str, df_name: str):
    spec = {
        "$schema": "https://vega.github.io/schema/vega-lite/v4.json",
        "description": f"Midas for {df_name}",
        "data": { "values": [] },
        "selection": {
            "brush": {
                "type": "interval"
            }
        },
        "mark": "point",
        "encoding": {
            "x": {"field": x_field, "type": "quantitative"},
            "y": {"field": y_field, "type": "quantitative"},
            "color": {
                "field": IS_OVERVIEW_FIELD_NAME, "type": "nominal",
                "scale": {"range": ["gray", "blue"]}
            }
        }
    }
    return spec
