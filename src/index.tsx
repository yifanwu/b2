import vegaEmbed, { Mode, EmbedOptions } from "vega-embed";
import { Spec, View } from "vega";
import { TopLevelSpec } from "vega-lite";
import React, { MouseEventHandler } from "react";
import ReactDOM from "react-dom";
export { default as vegaEmbed } from "vega-embed";

import $ from "jquery";
import "jqueryui";

import "./floater.css";

import { makeComm } from "./comm";
import MidasContainer from "./components/MidasContainer";
import { LogSteps } from "./utils";

import {SelectionShelf} from "./components/SelectionShelf";
import { ColumnShelf } from "./components/ColumnShelf";


declare global {
  interface Window {
    midas: MidasContainer;
    selectionShelf: SelectionShelf;
    columnShelf: ColumnShelf;
  }
}


export function load_ipython_extension() {
  createMidasComponent();
}


/**
 * Makes the resizer that allows changing the width of the sidebar.
 * @param divToResize the div representing the sidebar.
 */
function makeResizer(divToResize: JQuery<HTMLElement>) {

  let resizer = $("<div id=\"resizer\">");
  divToResize.append(resizer);

  resizer.on("mousedown", (e) => {
    let x = e.clientX;
    let originalWidth = divToResize.width();
    let originalWidth2 = $("#midas-react-wrapper").width();

    $(window).on("mousemove", (e) => {
      let delta = x - e.clientX;
      console.log(delta);
      divToResize.width((_, currentWidth) => originalWidth + delta);
      $("#midas-react-wrapper").width(originalWidth2 + delta);
    });
  });

  $(window).on("mouseup", () => {
    $(window).off("mousemove");
  });
}


export function createMidasComponent() {
  LogSteps("createMidasComponent", "this should be called only once!");

  let floater = $("<div id=\"midas-floater-wrapper\"/>");
  let reactWrapper = $("<div id=\"midas-react-wrapper\">");

  makeResizer(floater);

  floater.append(reactWrapper);

  $("#notebook").append(floater);

  ReactDOM.render(<MidasContainer ref={(comp) => makeComm(comp)} />,
    document.getElementById("midas-react-wrapper"));

  $([Jupyter.events]).on("kernel_starting.Kernel", function(){
    console.log("Kernel starting.");
//      resetSideBarState();
  });
  // $("#midas-floater-wrapper").css("position", "fixed");
  $("#midas-floating-container").height($("#midas-floater-wrapper").innerHeight);
}

function javascriptIndex(selector: string, outputs: any) {
  // Return the index in the output array of the JS repr of this viz
  for (let i = 0; i < outputs.length; i++) {
    const item = outputs[i];
    if (
      item.metadata &&
      item.metadata["midas"] === selector &&
      item.data["application/javascript"] !== undefined
    ) {
      return i;
    }
  }
  return -1;
}

function imageIndex(selector: string, outputs: any) {
  // Return the index in the output array of the PNG repr of this viz
  for (let i = 0; i < outputs.length; i++) {
    const item = outputs[i];
    if (
      item.metadata &&
      item.metadata["midas"] === selector &&
      item.data["image/png"] !== undefined
    ) {
      return i;
    }
  }
  return -1;
}

function showError(el: HTMLElement, error: Error) {
  el.innerHTML = `<div class="error">
    <p>Javascript Error: ${error.message}</p>
    <p>This usually means there's a typo in your chart specification.
    See the JavaScript console for the full traceback.</p>
  </div>`;

  throw error;
}

export function render(
  selector: string,
  spec: Spec | TopLevelSpec,
  type: Mode,
  opt: EmbedOptions,
  output_area: any
) {
  // Find the indices of this visualizations JS and PNG
  // representation.
  const imgIndex = imageIndex(selector, output_area.outputs);
  const jsIndex = javascriptIndex(selector, output_area.outputs);

  // If we have already rendered a static image, don't render
  // the JS version or append a new PNG version
  if (imgIndex > -1 && jsIndex > -1 && imgIndex === jsIndex + 1) {
    return;
  }

  // Never been rendered, so render JS and append the PNG to the
  // outputs for the cell
  const el = document.getElementById(selector.substring(1));
  vegaEmbed(el, spec, {
    loader: { http: { credentials: "same-origin" } },
    ...opt,
    mode: type
  })
    .then(result => {
      result.view
        .toImageURL("png")
        .then(imageData => {
          if (output_area !== undefined) {
            const output = {
              data: {
                "image/png": imageData.split(",")[1]
              },
              metadata: { "midas": selector },
              output_type: "display_data"
            };
            // This appends the PNG output, but doesn't render it this time
            // as the JS version will be rendered already.
            output_area.outputs.push(output);
          }
        })
        .catch(error => showError(el, error));
    })
    .catch(error => showError(el, error));
}