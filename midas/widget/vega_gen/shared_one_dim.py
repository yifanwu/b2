from midas.defaults import BRUSH_MARK, X_SCALE, X_PIXEL_SIGNAL, SELECTION_SIGNAL, CHART_HEIGHT

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
                        # there is something weird with using \", so switching to '
                        f"!event.item || event.item.mark.name !== '{BRUSH_MARK}'"
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
                            f"!event.item || event.item.mark.name !== '{BRUSH_MARK}'"
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
            "name": SELECTION_SIGNAL,
            "on": [
                {
                "events": {"signal": f"{X_PIXEL_SIGNAL}"},
                "update": f"span({X_PIXEL_SIGNAL}) ? {{x: invert('{X_SCALE}', {X_PIXEL_SIGNAL})}} : null"
                }
            ]
        }
    ]


def gen_x_brush_mark():
    return {
        "type": "rect",
        "name": BRUSH_MARK,
        "encode": {
            "enter": {
                "y": {"value": 0},
                "height": {"value": CHART_HEIGHT},
                "fill": {"value": "#333"},
                "fillOpacity": {"value": 0.2}
            },
            "update": {
                "x": {"signal": f"{X_PIXEL_SIGNAL}[0]"},
                "x2": {"signal": f"{X_PIXEL_SIGNAL}[1]"}
            }
        }
    }