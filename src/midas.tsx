import React, { MouseEventHandler } from "react";
import ReactDOM from "react-dom";
import MidasContainer from "./components/MidasContainer";
import MidasMidbar from "./components/MidasMidbar";
import {SelectionShelf} from "./components/SelectionShelf";
import { makeComm } from "./comm";
import "./floater.css";

import $ from "jquery";
import "jqueryui";
import { ColumnShelf } from "./components/ColumnShelf";

// TODO: extract HTML class names so there aren't so many strings everywhere


declare global {
  interface Window {
    midas: MidasContainer;
    selectionShelf: SelectionShelf;
    columnShelf: ColumnShelf;
  }
}

export function resetSideBarState() {
  console.log("Resetting sidebar state.");
  if (window.midas === undefined) {
    return;
  }

  window.midas.resetState();
}

/**
 * Adds the visualization of the data frame to the sidebar.
 * @param id the id of the data frame
 * @param df_name the name of the data frame
 */
export function addDataFrame(id: number, dfName: string, fixYScale: () => void, cb: () => void) {
  console.log("Adding data frame: " + dfName + " " + id);
  if (window.midas === undefined) {
    return;
  }
  window.midas.addDataFrame(id, dfName, fixYScale, cb);
}


export function addShelfItem(selectionName: string) {
  console.log("Adding selection to shelf");

  if (window.midas === undefined) {
    return;
  }

  window.selectionShelf.addSelectionItem(selectionName);
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
  let midbar = $("<div id=\"midbar\"/>");
 
  makeResizer(floater);
 
  floater.append(midbar);
  floater.append(reactWrapper);

  $("#notebook").append(floater);
  ReactDOM.render(<MidasMidbar/>, document.getElementById("midbar"));


  ReactDOM.render(<MidasContainer ref={(comp) => window.midas = comp} />, document.getElementById("midas-react-wrapper"));

  makeComm();

  // $("#midas-floater-wrapper").css("position", "fixed");
  $("#midas-floating-container").height($("#midas-floater-wrapper").innerHeight);
}