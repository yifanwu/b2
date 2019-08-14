import "./floater.css";

import $ from "jquery";
import "jqueryui";

// TODO: extract HTML class names so there aren't so many strings everywhere


export function addDataFrame(element: any, id: number, df_name: string) {
  let myId = `midas-element-${id}`;
  let div = $(`<div id=${myId}/>`);
  div.addClass("midas-element");

  if ($("#" + myId).length === 0) {
    $("#midas-floater-container").append(div);
  } else {
    let oldDiv = $(`#${myId}`);
    oldDiv.replaceWith(div);
  }
  div.append(element);

  let get_python_button = $("<button/>", {
      text: "code",
      click: () => {
        const execute = `m.js_get_current_chart_code('${df_name}')`;
        console.log("clicked, and executing", execute);
        IPython.notebook.kernel.execute(execute);
      },
  });
  get_python_button.css("align-self", "center");
  get_python_button.css("margin-right", 0);
  get_python_button.css("font-family", "monospace");

  div.append(get_python_button);

  let close_button = $("<button/>", {
      text: "x",
      click: () => {
        div.remove();
      },
   });
   close_button.css("align-self", "center");
   close_button.css("margin-right", 0);
   close_button.css("font-family", "monospace");

  div.append(close_button);
}

function createContainer() {
  let container = $("<div id=\"midas-floater-container\"/>");
  return container;
}

export function createFloater() {
  let floater = $("<div id=\"midas-floater-wrapper-fixed\"/>");

  $("#notebook-container").after(floater);
  // makeResizable();
  // makeDraggable();
  // floater.append(makeHeader);
  floater.append(createContainer);

  // $("#midas-floater-wrapper").css("position", "fixed");

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

