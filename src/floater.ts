import "./floater.css";

import $ from "jquery";
import "jqueryui";
import { contains } from "vega-lite/build/src/util";

// TODO: extract HTML class names so there aren't so many strings everywhere

let id = 0;

export function addDataFrame(element: any) {



  let myId = `midas-element-${id++}`;
  let div = $(`<div id=${myId}/>`);
  div.addClass("midas-element");

  $("#midas-floater-container").append(div);

  let button = $("<button/>", {
      text: "x",
      click: () => {
        div.remove();
      },
   });
   button.css("align-self", "center");
   button.css("margin-right", 0);
   button.css("font-family", "monospace");

  div.append(element);
  div.append(button);
}

function createContainer() {
  let container = $("<div id=\"midas-floater-container\"/>");
  return container;
}

export function createFloater() {
  let floater = $("<div id=\"midas-floater-wrapper\"/>");

  $("body").append(floater);

  makeResizable();
  makeDraggable();
  floater.append(makeHeader);
  floater.append(createContainer);

  $("#midas-floater-wrapper").css("position", "fixed");

  $("#midas-floating-container").height($("#midas-floater-wrapper").innerHeight);
}

function makeHeader() {
  return $("<div id=\"midas-floater-header\">")
    .addClass("header")
    .text("Midas Monitor");
}

function makeDraggable() {
  $("#midas-floater-wrapper").draggable({
    drag: function (event: any, ui: any) { },
    start: function (event: any, ui: any) {
      $(this).width($(this).width());
    },
    stop: function (event: any, ui: any) {
      $("#midas-floater-wrapper").css("position", "fixed");

    },
    handle: "#midas-floater-header"
  });
}

function makeResizable() {
  $("#midas-floater-wrapper").resizable({
    resize: function (event: any, ui: any) {
      // $('#varInspector').height($('#varInspector-wrapper').height() - $('#varInspector-header').height());
    },
    start: function (event: any, ui: any) {
      // $(this).width($(this).width());
      $(this).css("position", "fixed");
    },
    stop: function (event: any, ui: any) {
      // Ensure position is fixed (again)
      $(this).css("position", "fixed");
    }
  });
}

