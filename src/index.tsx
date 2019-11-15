import vegaEmbed, { Mode, EmbedOptions } from "vega-embed";
import { Spec, View } from "vega";
import { TopLevelSpec } from "vega-lite";
import React, { MouseEventHandler } from "react";
import ReactDOM from "react-dom";
export { default as vegaEmbed } from "vega-embed";

import $ from "jquery";
import "jqueryui";

import "./elements.css";
import "./sidebar.css";

import { makeComm } from "./comm";
import MidasContainer from "./components/MidasContainer";
import {MidasSidebar} from "./components/MidasSidebar";
import { LogSteps } from "./utils";

import {SelectionShelf} from "./components/SelectionShelf";
import { ProfilerShelf } from "./components/ProfilerShelf";


declare global {
  interface Window {
    midas: MidasContainer;
    selectionShelf: SelectionShelf;
    profilerShelf: ProfilerShelf;
  }
}


export function load_ipython_extension() {
  createMidasComponent();

  // @ryan was this ever fixed?
  $([Jupyter.events]).on("kernel_created.Kernel", function() {
    LogSteps("!!Kernel starting!!");
    createMidasComponent(false);
  });
}


/**
 * Makes the resizer that allows changing the width of the sidebar.
 * @param divToResize the div representing the sidebar.
 */
function makeResizer(onChange: (delta: number) => void) {

  let resizer = $("#midas-resizer");

  resizer.on("mousedown", (e) => {
    let x = e.clientX;
    let lastTotalMove = 0;

    $(window).on("mousemove", (e) => {
      let totalMove = x - e.clientX;
      let delta = totalMove - lastTotalMove;
      lastTotalMove = totalMove;

      onChange(delta);
    });
  });

  $(window).on("mouseup", () => {
    $(window).off("mousemove");
  });
}

function syncWidth(parentSelector: string, childSelector: string, marginAdjust = 0) {
  let parentwidth = $(parentSelector).width();
  $(childSelector).width(parentwidth - marginAdjust );
}

export function createMidasComponent(is_first_time: boolean = true) {
  LogSteps("createMidasComponent");

  if (is_first_time) {
    $(window).resize(function() {
      syncWidth("#midas-sidebar-wrapper", ".midas-inside", 10);
    });
    const midasSideBarDiv = $("<div id=\"midas-sidebar-wrapper\"/>");
    $("#notebook").append(midasSideBarDiv);
  }

  ReactDOM.render(<MidasSidebar ref={(comp) => makeComm(comp)}/>, document.getElementById("midas-sidebar-wrapper"));

  if (is_first_time) {
    makeResizer((delta) => {
      let oldWidth = $("#midas-sidebar-wrapper").width();
      $("#midas-sidebar-wrapper").width(oldWidth + delta);
      syncWidth("#midas-sidebar-wrapper", ".midas-inside", 10 * 2);
    });
    syncWidth("#midas-sidebar-wrapper", ".midas-inside", 10 * 2);
  }
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
