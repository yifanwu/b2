import React, { MouseEventHandler, ReactElement } from "react";
import ReactDOM from "react-dom";

import "./floater.css";

import $ from "jquery";
import "jqueryui";
import { any } from "prop-types";

// TODO: extract HTML class names so there aren't so many strings everywhere


interface DeleteButtonProps {
  onClick: MouseEventHandler;
}

interface ContainerState {
  elements: ContainerElementState[];
}

interface ContainerElementState {
  key: number;
  element: string;
  name: string;
}

interface MidasElementProps {
  key: number;
  element: any;
  onClick: MouseEventHandler;
  name: string;
}

function DeleteButton(props: DeleteButtonProps): ReactElement {
  return (
    <button className="delete-button" onClick={props.onClick}>
      x
    </button>
  );
}

function MidasElement(props: MidasElementProps) {
  return (
    <div className={`midas-element-${props.key}`}>
      <p>test</p>
    </div>
  );
}

class MidasContainer extends React.Component<any, ContainerState> {
  constructor(props?: any) {
    super(props);
    this.state = {
      elements: [],
    };
  }

  addDataFrame(element: any, key: number, dfName: string) {
    let newElements = this.state.elements.concat([{
      element: JSON.stringify(element),
      key: key,
      name: dfName,
    }]);

    this.setState({elements: newElements});
    console.log("state", this.state);
  }

  render() {
    return (
      <div id="midas-floater-container">
        {this.state.elements.map(({key, element, name}) => (
          <MidasElement
            key={key}
            element={element}
            name={name}
            onClick={() => 3}/>
        ))}
      </div>
    );
  }
}

// @ts-ignore
let container: MidasContainer = <MidasContainer/>;

export function addDataFrame(element: any, id: number, df_name: string) {
  console.log("The container is ", container);
  if (container != null) {
    container.addDataFrame(element, id, df_name);
  }
}

function addDataFrameold(element: any, id: number, df_name: string) {
  let myId = `midas-element-${id}`;
  let div = $(`<div id=${myId}/>`);
  div.addClass("midas-element");

  if ($("#" + myId).length === 0) {
    $("#midas-floater-container").append(div);
    console.log("Appending div...");
  } else {
    let oldDiv = $(`#${myId}`);
    oldDiv.replaceWith(div);
    console.log("Replacing div...");
  }

  let get_python_button = $("<button/>", {
    text: "codeaaaa",
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
  console.log("appending python button...");

//  ReactDOM.render(DeleteButton({ onClick: () => div.remove() }), document.getElementById(myId));

  div.append(element);
}

export function createFloater() {
  let floater = $("<div id=\"midas-floater-wrapper\"/>");


  $("body").append(floater);


  // @ts-ignore
  container = <MidasContainer/>;

  // @ts-ignore
  ReactDOM.render(container, document.getElementById("midas-floater-wrapper"));

  //  makeResizable();
  //  makeDraggable();
  // floater.append(makeHeader);
//  floater.append(createContainer);

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

