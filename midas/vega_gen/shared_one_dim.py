
from .defaults import BRUSH_MARK, X_SCALE, X_PIXEL_SIGNAL, X_SELECT_SIGNAL, CHART_WIDTH, CHART_HEIGHT

def gen_click_signal():
    return {
        "name": "click",
        "value": {},
        "on": [
            {
                "events": "rect:click",
                "update": "datum"
            }
        ]
    }


def gen_x_brush_signal():
    return [
        {
            "name": X_PIXEL_SIGNAL,
            "value": [0, 0],
            "on": [
                {
                    "events": "mousedown",
                    "update": "[x(), x()]"
                },
                {
                    "events": "[mousedown, window:mouseup] > window:mousemove!",
                    "update": f"[{X_PIXEL_SIGNAL}[0], clamp(x(), 0, width)]"
                },
                {
                    "events": {"signal": "delta"},
                    "update": "clampRange([anchor[0] + delta, anchor[1] + delta], 0, width)"
                }
            ]
        },
        {
            "name": "anchor",
            "value": None,
            "on": [{"events": f"@{BRUSH_MARK}:mousedown", "update": f"slice({X_PIXEL_SIGNAL})"}]
        },
        {
            "name": "xdown",
            "value": 0,
            "on": [{"events": f"@{BRUSH_MARK}:mousedown", "update": "x()"}]
        },
        {
        "name": "delta",
        "value": 0,
        "on": [
            {
                "events": f"[@{BRUSH_MARK}:mousedown, window:mouseup] > window:mousemove!",
               "update": "x() - xdown"
            }]
        },
        {
            "name": X_SELECT_SIGNAL,
            "on": [
                {
                "events": {"signal": f"{X_PIXEL_SIGNAL}"},
                "update": f"span({X_PIXEL_SIGNAL}) ? invert(\"{X_SCALE}\", {X_PIXEL_SIGNAL}) : null"
                }
            ]
        }
    ]

