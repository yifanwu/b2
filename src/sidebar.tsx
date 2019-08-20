import React, { MouseEventHandler } from "react";
import ReactDOM from "react-dom";

import { X_SCALE, Y_SCALE, X_DOMAIN_SIGNAL, Y_DOMAIN_SIGNAL } from "./constants";
import "./floater.css";

import $ from "jquery";
import "jqueryui";
import { DOMWidgetModel } from "@jupyter-widgets/base";

// TODO: extract HTML class names so there aren't so many strings everywhere

declare global {
  interface Window { sidebar: MidasContainer; }
}

interface ContainerState {
  elements: ContainerElementState[];
  idToCell: Map<string, number>;
}

interface ContainerElementState {
  id: number;
  name: string;
  fixYScale: () => void;
}

interface MidasElementProps {
  id: number;
  onClick: MouseEventHandler;
  name: string;
  getCellId: Function;
  fixYScale: () => void;
}

interface MidasElementState {
  hidden: boolean;
}


/**
 * Returns the DOM id of the given element that contains the visualizations
 * @param id the id of the data frame of the visualization
 * @param includeSelector whether to include CSS selector (#)
 */
export function makeElementId(id: number, includeSelector: boolean = false) {
  let toReturn = `midas-element-${id}`;
  return includeSelector ? "#" + toReturn : toReturn;
}

/**
 * Contains the visualization as well as a header with actions to minimize,
 * delete, or find the corresponding cell of the visualization.
 */
class MidasElement extends React.Component<MidasElementProps, MidasElementState> {
  constructor(props: any) {
    super(props);
    this.state = { hidden: false };
  }

  /**
   * Toggles whether the visualization can be seen
   */
  toggleHiddenStatus() {
    this.setState(prevState => {
      return { hidden: !prevState.hidden };
    });
  }
  /**
   * Selects the cell in the notebook where the data frame was defined.
   * Note that currently if the output was generated and then the page
   * is refreshed, this may not work.
   */
  selectCell() {
    let cell = Jupyter.notebook.get_msg_cell(this.props.getCellId());
    let index = Jupyter.notebook.find_cell_index(cell);
    Jupyter.notebook.select(index);
  }

  getPythonButtonClicked() {
    const execute = `m.js_get_current_chart_code('${this.props.name}')`;
    console.log("clicked, and executing", execute);
    IPython.notebook.kernel.execute(execute);
  }

  /**
   * Renders this component.
   */
  render() {
    return (
      <div className="midas-element">
        <div className="midas-header">
          <span className="midas-title">{this.props.name}</span>
          <div className="midas-header-options"></div>
          <button
            className={"midas-header-button"}
            onClick={() => this.props.fixYScale()}>
            Fix Y
          </button>
          <button
            className={"midas-header-button"}
            onClick={() => this.getPythonButtonClicked()}>
            Code
          </button>
          <button
            className={"midas-header-button"}
            onClick={() => this.selectCell()}
          >Cell</button>
          <button
            className={"midas-header-button"}
            onClick={() => this.toggleHiddenStatus()}>
            {this.state.hidden ? "+" : "-"}
          </button>
          <button
            className={"midas-header-button"}
            onClick={(e) => this.props.onClick(e)}>
            x
          </button>

        </div>
        <div
          id={makeElementId(this.props.id)}
          style={this.state.hidden ? { display: "none" } : {}}
        />
      </div>
    );
  }
}

/**
 * Container for the MidasElements that hold the visualization.
 */
class MidasContainer extends React.Component<any, ContainerState> {
  constructor(props?: any) {
    super(props);
    this.state = {
      elements: [],
      idToCell: new Map(),
    };
  }

  /**
   * Looks up the id of the notebook cell from which the given data frame was
   * defined.
   * @param name the name of the data frame
   */
  getCellId(name: string) {
    return this.state.idToCell[name];
  }

  /**
   * Stores the cell id at which the given data frame was defined.
   * @param name the name of the data frame
   * @param cell the cell id at which the data frame was defined
   */
  recordDFCellId(name: string, cell: string) {
    this.setState((prevState) => {
      prevState.idToCell[name] = cell;
      return {
        elements: prevState.elements,
        idToCell: prevState.idToCell,
      };
    });
  }

  /**
   * Adds the visualization of the given data frame to this container
   * @param id the id of the data frame
   * @param dfName the name of the data frame
   */
  addDataFrame(id: number, dfName: string, fixYScale: () => void, cb: () => void) {
    let shouldReturn = false;
    // todo: make less janky/more idiomatic?
    this.state.elements.forEach((e) => {
      if (id === e.id) {
        shouldReturn = true;
      }
    });

    if (shouldReturn) return;

    this.setState(prevState => {
      prevState.elements.push({
        id: id,
        name: dfName,
        fixYScale: fixYScale,
      });
      return prevState;
     }, cb);
     console.log("State " + JSON.stringify(this.state));
  }

  /**
   * Removes the given data frame via id
   * @param key the id of the data frame
   */
  removeDataFrame(id: number) {
    this.setState(prevState => {
      return {
        elements: prevState.elements.filter(e => (e.id !== id))
      };
    });
  }

  /**
   * Renders this component.
   */
  render() {
    return (
      <div id="midas-floater-container">
        {this.state.elements.map(({ id, name, fixYScale }, index) => (
          <MidasElement id={id} key={id} name={name} onClick={() => this.removeDataFrame(id)} getCellId={() => this.getCellId(name)} fixYScale={() => fixYScale()} />
        ))}
      </div>
    );
  }
}

/**
 * Adds the visualization of the data frame to the sidebar.
 * @param id the id of the data frame
 * @param df_name the name of the data frame
 */
export function addDataFrame(id: number, df_name: string, fixYScale: () => void, cb: () => void) {
  console.log("Adding data frame: " + df_name + " " + id);
  if (window.sidebar === undefined) {
    return;
  }
  window.sidebar.addDataFrame(id, df_name, fixYScale, cb);
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

/**
 * Makes the comm responsible for discovery of which visualization
 * corresponds to which cell, accomplished through inspecting the
 * metadata of the message sent.
 */
function makeComm() {
  Jupyter.notebook.kernel.comm_manager.register_target('midas-cell-comm',
    function (comm: any, msg: any) {
      // comm is the frontend comm instance
      // msg is the comm_open message, which can carry data

      // Register handlers for later messages:
      comm.on_msg(function (msg: any) {
        let cellId = msg.parent_header.msg_id;

        console.log(msg.content.data.name, cellId);
        window.sidebar.recordDFCellId(msg.content.data.name, cellId);
      });
      comm.on_close(function (msg: any) { });
    });

}

/**
 * Creates the sidebar.
 */
export function createSidebar() {
  let floater = $("<div id=\"midas-floater-wrapper\"/>");
  let reactWrapper = $("<div id=\"midas-react-wrapper\">");

  makeResizer(floater);

  floater.append(reactWrapper);

  $("#notebook").append(floater);


  ReactDOM.render(<MidasContainer ref={(comp) => window.sidebar = comp} />, document.getElementById("midas-react-wrapper"));

  makeComm();


  // $("#midas-floater-wrapper").css("position", "fixed");
  $("#midas-floating-container").height($("#midas-floater-wrapper").innerHeight);
}


