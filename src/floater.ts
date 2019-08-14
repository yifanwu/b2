import "./floater.css";
import { View } from "vega";

import $ from "jquery";
import "jqueryui";
import { X_SCALE, Y_SCALE, X_DOMAIN_SIGNAL, Y_DOMAIN_SIGNAL } from "./constants";

// TODO: extract HTML class names so there aren't so many strings everywhere

const btnClass = "chart-btns";

// TODO: we should really start using React, this is really ugly

export function addDataFrame(element: any, id: number, df_name: string, view: View) {
  let myId = `midas-element-${id}`;
  let div = $(`<div id=${myId}/>`);

  if ($("#" + myId).length === 0) {
    $("#midas-floater-container").append(div);
  } else {
    let oldDiv = $(`#${myId}`);
    oldDiv.replaceWith(div);
  }
  div.append(element);

  let buttonDiv = $(`<div/>`).addClass("midas-element");
  const get_python_button = $("<button/>", {
      text: "code",
      click: () => {
        const execute = `m.js_get_current_chart_code('${df_name}')`;
        console.log("clicked, and executing", execute);
        IPython.notebook.kernel.execute(execute);
      },
    }).addClass(btnClass);
  buttonDiv.append(get_python_button);

  // TODO: place this next to the y axis
  const fix_y_scale_button = $("<button/>", {
      text: "fix y",
      click: () => {
        // access the current scale
        // @ts-ignore
        const y_scale = view.scale(Y_SCALE);
        // then set the current scale
        view.signal(Y_DOMAIN_SIGNAL, y_scale.domain());
      },
    }).addClass(btnClass);

  buttonDiv.append(fix_y_scale_button);

  // x is problematic
  // TODO: place this next to the x axis
  // const fix_x_scale_button = $("<button/>", {
  //   text: "fix x",
  //   click: () => {
  //     // access the current scale
  //     const x_scale = view.scale(X_SCALE);
  //     // then set the current scale
  //     view.signal(X_DOMAIN_SIGNAL, x_scale.domain());
  //   },
  // }).addClass(btnClass);

  // buttonDiv.append(fix_x_scale_button);

  let close_button = $("<button/>", {
      text: "x",
      click: () => {
        div.remove();
      },
    }).addClass(btnClass);
  buttonDiv.append(close_button);
  div.append(buttonDiv);
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

