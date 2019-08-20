import React, { MouseEventHandler } from "react";
import ReactDOM from "react-dom";
import MidasContainer from "./components/MidasContainer";

import { makeComm } from "./comm";
import "./floater.css";

import $ from "jquery";
import "jqueryui";
import { DOMWidgetModel } from "@jupyter-widgets/base";

// TODO: extract HTML class names so there aren't so many strings everywhere


declare global {
  interface Window { midas: MidasContainer; }
}



/**
 * Adds the visualization of the data frame to the sidebar.
 * @param id the id of the data frame
 * @param df_name the name of the data frame
 */
export function addDataFrame(id: number, df_name: string, fixYScale: () => void, cb: () => void) {
  console.log("Adding data frame: " + df_name + " " + id);
  if (window.midas === undefined) {
    return;
  }
  window.midas.addDataFrame(id, df_name, fixYScale, cb);
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
  let floater = $("<div id=\"midas-floater-wrapper\"/>");
  let reactWrapper = $("<div id=\"midas-react-wrapper\">");

  makeResizer(floater);

  floater.append(reactWrapper);

  $("#notebook").append(floater);


  ReactDOM.render(<MidasContainer ref={(comp) => window.midas = comp} />, document.getElementById("midas-react-wrapper"));

  makeComm();

  // $("#midas-floater-wrapper").css("position", "fixed");
  $("#midas-floating-container").height($("#midas-floater-wrapper").innerHeight);
}