import { IS_OVERVIEW_FIELD_NAME, CHART_HEIGHT } from "../constants";
import { LogInternalError } from "../utils";

type SelectionType = "multiclick" | "brush" | "none";
export type SelectionDimensions = "" | "x" | "y" | "xy";
type SortType = "x" | "-x" | "y" | "-y" | "";

// note that this is synced with the vis_types.py file
export interface EncodingSpec {
  mark: "bar" | "circle" | "line";
  x: string;
  xType: "ordinal" | "quantitative" | "temporal";
  y: string;
  yType: "ordinal" | "quantitative" | "temporal";
  selectionType: SelectionType;
  selectionDimensions: SelectionDimensions;
  sort: SortType;
  size?: string;
}

export function multiSelectedField(e: EncodingSpec) {
  if ((e.selectionDimensions === "x") || (e.selectionDimensions === "y")) {
    return e[e.selectionDimensions];
  }
  return LogInternalError("cannot call multiSelectedField on such spec");
}

const colorSpec = {
  "field": IS_OVERVIEW_FIELD_NAME, "type": "nominal",
  "scale": {"range": ["#003E6B", "#9FB3C8"], "domain": [false, true]},
  // @ts-ignore
  "legend": null
};

const selectedColorSpec = {
  "field": IS_OVERVIEW_FIELD_NAME, "type": "nominal",
  "scale": {"range": ["#fd8d3c", "#fdae6b"], "domain": [false, true]},
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
    // "resolve": "union",
    // "on": "[mousedown[event.shiftKey], window:mouseup] > window:mousemove!",
    // "translate": "[mousedown[event.shiftKey], window:mouseup] > window:mousemove!",
    // @ts-ignore
    // "zoom": null
    // the following is needed for the brush layer to not activate
    "empty": "none"
  };
  if (selectionKind === "x") {
    result["encodings"] = ["x"];
  } else if (selectionKind === "y") {
    result["encodings"] = ["y"];
  }
  return result;
}

function getSelectionDimensionsToArray(s: SelectionDimensions) {
  if (s === "") {
    LogInternalError("Should only be called if there are selection dimensions");
  }
  return s.split("");
}

function genSelection(selectionType: SelectionType, selectionDimensions: SelectionDimensions) {
  if (selectionDimensions === "") {
    return {
      // "zoom": zoomSelection
    };
  }
  if (selectionType === "multiclick") {
    return {
      // "zoom": zoomSelection,
      "select": {
        "type": "multi",
        "encodings": getSelectionDimensionsToArray(selectionDimensions),
        // note that this empty is important for the selections to work
        "empty": "none"
      }
    };
  }
  if (selectionType === "brush") {
    return {
      // "zoom": zoomSelection,
      "brush": brushSelection(selectionDimensions)
    };
  }
  LogInternalError(`Only two selection types are supported, but you specified ${selectionType}`);
  // roll with it?
  return {
    // "zoom": zoomSelection
  };
}

function genSelectionReference(selectionType: SelectionType) {
  if (selectionType === "multiclick") {
    return "select";
  }
  return "brush";
}

function modifySpecForSort(spec: any, sort: SortType, x: string, y: string) {

  if ((sort === "y") || (sort === "-y")) {
    spec["transform"] = [{
      "calculate": `datum.is_overview ? datum['${y}'] : null`,
      "as": "sort_order"
    }];
    const order = (sort === "-y")
      ? "descending"
      : "ascending"
      ;
    spec["encoding"]["x"]["sort"] = {"field": "sort_order", "order": order};

  } else if ((sort === "x") || (sort === "-x")) {
    spec["transform"] = [{
      "calculate": `datum.is_overview ? datum['${x}'] : null`,
      "as": "sort_order"
    }];
    const order = (sort === "-x")
      ? "descending"
      : "ascending"
      ;
      spec["encoding"]["y"]["sort"] = {"field": "sort_order", "order": order};
  }
  // modify in place
  return;
}


export function genVegaSpec(encoding: EncodingSpec, dfName: string, data: any[]) {
  switch (encoding.mark) {
    case "bar": {
      let barSpec = {
        "$schema": "https://vega.github.io/schema/vega-lite/v4.json",
        "description": `Midas Generated Visualization of dataframe ${dfName}`,
        "height": CHART_HEIGHT,
        "data": {
          "values": data
        },
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
          "opacity": {
            "value": 0.5
          },
        },
      };
      if (encoding.selectionDimensions === "") {
        barSpec["mark"] = "bar";
        barSpec["encoding"]["color"] = colorSpec;
      } else {
        barSpec["layer"] = [
          {
            "mark": {"type": "bar",  "tooltip": true},
            "encoding": {
              "color": colorSpec
            },
            "selection": genSelection(encoding.selectionType, encoding.selectionDimensions),
          },
          {
            "mark": {"type": "bar",  "tooltip": true},
            "transform": [
              {
                "filter": {
                  "selection": genSelectionReference(encoding.selectionType)
                }
              }
            ],
            "encoding": {
              "color": selectedColorSpec
            }
          }
        ];
        barSpec["resolve"] = {"scale": {"color": "independent"}};
      }
      modifySpecForSort(barSpec, encoding.sort, encoding.x, encoding.y);
      return barSpec;
    }
    case "circle": {
      const circleSpec = {
        "$schema": "https://vega.github.io/schema/vega-lite/v4.json",
        "height": CHART_HEIGHT,
        "description": `Midas for ${dfName}`,
        "data": { "values": data },
        "selection": genSelection(encoding.selectionType, encoding.selectionDimensions),
        "mark": {"type": "point",  "tooltip": true},
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
      // if this is click, then we need to add extra highlighting
      if (encoding.selectionType === "multiclick") {
        circleSpec["encoding"]["fill"] = {
          "condition": [{"test": {"selection": "select"}, "value": "red"}],
          "value": "none"
        };
      }

      modifySpecForSort(circleSpec, encoding.sort, encoding.x, encoding.y);
      return circleSpec;
    }
    case "line": {
      const lineSpec = {
        "$schema": "https://vega.github.io/schema/vega-lite/v4.json",
        "description": dfName,
        "height": CHART_HEIGHT,
        "data": { "values": data },
        "selection": genSelection(encoding.selectionType, encoding.selectionDimensions),
        "mark": "line",
        "encoding": {
            "x": {"field": encoding.x, "type": encoding.xType},
            "y": {"field": encoding.y, "type": encoding.yType},
            "color": colorSpec,
        },
        "opacity": {"value": 0.5}
      };
      modifySpecForSort(lineSpec, encoding.sort, encoding.x, encoding.y);
      return lineSpec;
    }
    default:
      throw Error(`${encoding.mark} not handled`);
  }
}