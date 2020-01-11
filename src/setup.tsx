import React from "react";
import ReactDOM from "react-dom";

import { MidasSidebar } from "./components/MidasSidebar";
import { MidasContainerFunctions } from "./types";

const SIDEBAR_ID = "midas-sidebar-wrapper";
const SIDEBAR_SELECTOR = `#${SIDEBAR_ID}`;
const SIDE_INSIDE_SELECTOR = "#midas-inside";
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
  $(childSelector).width(parentwidth - marginAdjust);
}

export function tearDownMidasComponent() {
  if ($(`#${SIDEBAR_ID}`).length !== 0) {
    ReactDOM.unmountComponentAtNode(document.getElementById(SIDEBAR_ID));
    $(SIDEBAR_SELECTOR).remove();
  }
}

export function createMidasComponent(
  columnSelectMsg: (col: string, table: string) => void,
  // makeSelectionFromShelf: (selection: string) => void,
  containerFunctions: MidasContainerFunctions
): MidasSidebar {
  if ($(SIDEBAR_SELECTOR).length === 0) {
    $(window).resize(function () {
      syncWidth(SIDEBAR_SELECTOR, SIDE_INSIDE_SELECTOR, 10);
    });
    const midasSideBarDiv = $(`<div id=\"${SIDEBAR_ID}\"/>`);
    $("#notebook").append(midasSideBarDiv);
  }

  let midasRef;
  ReactDOM.render(<MidasSidebar
    ref={(comp) => midasRef = comp}
    columnSelectMsg={columnSelectMsg}
    midasElementFunctions={containerFunctions}
    // makeSelectionFromShelf={makeSelectionFromShelf}
  />, document.getElementById(SIDEBAR_ID));

  makeResizer((delta) => {
    let oldWidth = $(SIDEBAR_SELECTOR).width();
    $(SIDEBAR_SELECTOR).width(oldWidth + delta);
    syncWidth(SIDEBAR_SELECTOR, SIDE_INSIDE_SELECTOR, 10 * 2);
  });
  syncWidth(SIDEBAR_SELECTOR, SIDE_INSIDE_SELECTOR, 10 * 2);
  return midasRef;
}
