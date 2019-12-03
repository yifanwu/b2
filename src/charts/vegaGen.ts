import { IS_OVERVIEW_FIELD_NAME } from "../constants";
import { TopLevelSpec } from "vega-lite";


export interface EncodingSpec {
  shape: string;
  x: string;
  y: string;
}

const colorSpec = {
  "field": IS_OVERVIEW_FIELD_NAME, "type": "nominal",
  "scale": {"range": ["blue", "gray"]},
  // @ts-ignore
  "legend": null
};

function genSelection(brush_only_x: boolean) {
  const spec = {
    "zoom": {
      "type": "interval",
      "bind": "scales",
      "translate": "[mousedown[!event.shiftKey], window:mouseup] > window:mousemove!",
      "zoom": "wheel!"
    },
    "brush": {
      "type": "interval",
      "resolve": "union",
      "on": "[mousedown[event.shiftKey], window:mouseup] > window:mousemove!",
      "translate": "[mousedown[event.shiftKey], window:mouseup] > window:mousemove!",
      // @ts-ignore
      "zoom": null
    }
  };
  if (brush_only_x) {
    spec["brush"]["encodings"] = ["x"];
  }
  return spec;
}

// TODO: TopLevelSpec
export function genVegaSpec(encoding: EncodingSpec, dfName: string, data: any[]) {
  switch (encoding.shape) {
    case "bar":
      return {
        "$schema": "https://vega.github.io/schema/vega-lite/v4.json",
        "description": `Midas Generated Visualization of dataframe ${dfName}`,
        "selection": genSelection(true),
        "data": {
          "values": data
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
              // @ts-ignore
              "stack": null
          },
          "color": colorSpec,
          "opacity": {"value": 0.7}
        }
      };
    case "circle":
      return {
        "$schema": "https://vega.github.io/schema/vega-lite/v4.json",
        "description": `Midas for ${dfName}`,
        "data": { "values": data },
        "selection": genSelection(false),
        "mark": "point",
        "encoding": {
          "x": {"field": encoding.x, "type": "quantitative"},
          "y": {"field": encoding.y, "type": "quantitative"},
          "color": colorSpec,
          "opacity": {"value": 0.7}
        }
      };
    case "line":
      return {
        "$schema": "https://vega.github.io/schema/vega-lite/v4.json",
        "description": dfName,
        "data": { "values": data },
        "mark": "line",
        "encoding": {
            "x": {"field": encoding.x, "type": "temporal"},
            "y": {"field": encoding.y, "type": "quantitative"}
        },
        "color": colorSpec,
        "opacity": {"value": 0.7}
      };
    default:
      throw Error(`${encoding.shape} not handled`);
  }
}