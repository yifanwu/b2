def gen_linechart_spec(x_field: str, y_field: str, df_name: str):
    spec = {
        "$schema": "https://vega.github.io/schema/vega-lite/v4.json",
        "description": df_name,
        "data": { "values": [] },
        "mark": "line",
        "encoding": {
            "x": {"field": x_field, "type": "temporal"},
            "y": {"field": y_field, "type": "quantitative"}
        }
    }
    return spec