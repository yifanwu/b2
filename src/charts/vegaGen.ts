import { IS_OVERVIEW_FIELD_NAME } from "../constants";
import { LogInternalError } from "../utils";

type SelectionType = "multiclick" | "brush";
type SelectionDimensions = "" | "x" | "y" | "xy";

export interface EncodingSpec {
  mark: "bar" | "circle" | "line";
  x: string;
  xType: "ordinal" | "quantitative" | "temporal";
  y: string;
  yType: "ordinal" | "quantitative" | "temporal";
  selectionType: SelectionType;
  selectionDimensions: SelectionDimensions;
  size?: string;
}

const colorSpec = {
  "field": IS_OVERVIEW_FIELD_NAME, "type": "nominal",
  "scale": {"range": ["#003E6B", "#9FB3C8"], "domain": [false, true]},
  // @ts-ignore
  "legend": null
};

// for the field "zoom", under top-level "selection"
const zoomSelection = {
  "type": "interval",
  "bind": "scales",
  "translate": "[mousedown[!event.shiftKey], window:mouseup] > window:mousemove!",
  "zoom": "wheel!"
};

// for the field "brush", under top-level "selection"
function brushSelection(selectionKind: SelectionDimensions) {
  let result = {
    "type": "interval",
    "resolve": "union",
    "on": "[mousedown[event.shiftKey], window:mouseup] > window:mousemove!",
    "translate": "[mousedown[event.shiftKey], window:mouseup] > window:mousemove!",
    // @ts-ignore
    "zoom": null
  };
  if (selectionKind === "x") {
    result["encodings"] = "x";
  } else if (selectionKind === "y") {
    result["encodings"] = "y";
  }
  return result;
}

function genSelection(selectionType: SelectionType, selectionDimensions: SelectionDimensions) {
  if (selectionDimensions === "") {
    return {
      "zoom": zoomSelection
    };
  }
  if (selectionType === "multiclick") {
    return {
      "zoom": zoomSelection,
      "select": multiClickSelection
    };
  }
  if (selectionType === "brush") {
    return {
      "zoom": zoomSelection,
      "brush": brushSelection(selectionDimensions)
    };
  }
  LogInternalError(`Only two selection types are supported, but you specified ${selectionType}`);
  // roll with it?
  return {
    "zoom": zoomSelection
  };
}

// for the field "select", under top-level "selection"
const multiClickSelection = {"type": "multi"};

export function genVegaSpec(encoding: EncodingSpec, dfName: string, data: any[]) {
  switch (encoding.mark) {
    case "bar":
      return {
        "$schema": "https://vega.github.io/schema/vega-lite/v4.json",
        "description": `Midas Generated Visualization of dataframe ${dfName}`,
        "selection": genSelection(encoding.selectionType, encoding.selectionDimensions),
        "data": {
          "values": data
        },
        "mark": "bar",
        "encoding": {
          "x": {
              "field": encoding.x,
              "type": encoding.xType
          },
          "y": {
              "field": encoding.y,
              "type": encoding.yType,
              // @ts-ignore
              "stack": null
          },
          "color": colorSpec,
          "opacity": {
            "value": 0.5
          },
          "stroke": {"value": "#F0B429"},
          "strokeWidth": {
            "condition": [
              {
                "test": {
                  "and": [
                    {"selection": "select"},
                    "length(data(\"select_store\"))"
                  ]
                },
                "value": 3
              }
            ],
            "value": 0
          }
        }
      };
    case "circle":
      return {
        "$schema": "https://vega.github.io/schema/vega-lite/v4.json",
        "description": `Midas for ${dfName}`,
        "data": { "values": data },
        "selection": genSelection(encoding.selectionType, encoding.selectionDimensions),
        "mark": "point",
        "encoding": {
          "x": {
            "field": encoding.x,
            "type": encoding.xType,
            "scale": {"zero": false}
          },
          "y": {"field": encoding.y, "type": encoding.yType},
          "color": colorSpec,
          "opacity": {"value": 0.5}
        }
      };
    case "line":
      return {
        "$schema": "https://vega.github.io/schema/vega-lite/v4.json",
        "description": dfName,
        "data": { "values": data },
        "selection": genSelection(encoding.selectionType, encoding.selectionDimensions),
        "mark": "line",
        "encoding": {
            "x": {"field": encoding.x, "type": encoding.xType},
            "y": {"field": encoding.y, "type": encoding.yType}
        },
        "color": colorSpec,
        "opacity": {"value": 0.5}
      };
    default:
      throw Error(`${encoding.mark} not handled`);
  }
}