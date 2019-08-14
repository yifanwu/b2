import React, { MouseEventHandler, ReactElement } from 'react';
import ReactDOM from 'react-dom';

import "./floater.css";

import $ from "jquery";
import "jqueryui";

// TODO: extract HTML class names so there aren't so many strings everywhere

let id = 0;

interface DeleteButtonProps {
  onClick: MouseEventHandler;
}

function DeleteButton(props: DeleteButtonProps): ReactElement {
  return (
    <button className="delete-button" onClick={props.onClick}>
      x
    </button>
  );
}

export function addDataFrame(element: any) {
  let myId = `midas-element-${id++}`;
  let div = $(`<div id=${myId}/>`);
  div.addClass("midas-element");

  $("#midas-floater-container").append(div);

  ReactDOM.render(DeleteButton({onClick: () => div.remove()}), document.getElementById(myId));

  div.append(element);
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

