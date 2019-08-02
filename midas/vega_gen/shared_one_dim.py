
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

def gen_x_brush_signal_core():
    return {  
        "name": X_PIXEL_SIGNAL,
        "value":[  
            0,
            0
        ],
        "on":[  
            {  
                "source":"scope",
                "events":{  
                    "type":"mousedown",
                    "filter":[  
                        f"!event.item || event.item.mark.name !== \"{BRUSH_MARK}\""
                    ]
                },
                "update":"[x(), x()]"
            },
            {  
                "events":{  
                    "source": "window",
                    "type": "mousemove",
                    "consume": True,
                    "between":[  
                    {  
                        "source":"scope",
                        "type":"mousedown",
                        "filter":[  
                            f"!event.item || event.item.mark.name !== \"{BRUSH_MARK}\""
                        ]
                    },
                    {  
                        "source":"window",
                        "type":"mouseup"
                    }
                    ]
                },
                "update": f"[{X_PIXEL_SIGNAL}[0], clamp(x(), 0, width)]"
            },
            {  
                "events":{  
                    "signal":"delta"
                },
                "update":"[anchor[0] + delta, anchor[1] + delta]"
            }
        ]
    }

def gen_x_brush_signal():
    core = gen_x_brush_signal_core()
    return [
        core,
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

