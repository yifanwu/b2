import React from "react";
import ReactDOM from "react-dom";

import { MidasSidebar } from "./components/MidasSidebar";
import { LogSteps } from "./utils";

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

export function createMidasComponent(is_first_time: boolean = true): MidasSidebar {
  LogSteps("createMidasComponent");

  if (is_first_time) {
    $(window).resize(function() {
      syncWidth("#midas-sidebar-wrapper", ".midas-inside", 10);
    });
    const midasSideBarDiv = $("<div id=\"midas-sidebar-wrapper\"/>");
    $("#notebook").append(midasSideBarDiv);
  }

  let midasRef;
  ReactDOM.render(<MidasSidebar ref={(comp) => midasRef = comp}/>, document.getElementById("midas-sidebar-wrapper"));

  if (is_first_time) {
    makeResizer((delta) => {
      let oldWidth = $("#midas-sidebar-wrapper").width();
      $("#midas-sidebar-wrapper").width(oldWidth + delta);
      syncWidth("#midas-sidebar-wrapper", ".midas-inside", 10 * 2);
    });
    syncWidth("#midas-sidebar-wrapper", ".midas-inside", 10 * 2);
  }
  return midasRef;
}
