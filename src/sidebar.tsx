import React, { MouseEventHandler, ReactElement } from "react";
import ReactDOM from "react-dom";
import { SortableContainer, SortableElement } from 'react-sortable-hoc';
import arrayMove from 'array-move';

import "./floater.css";

import $ from "jquery";
import "jqueryui";

// TODO: extract HTML class names so there aren't so many strings everywhere

export function makeElementId(id: number, includeSelector: boolean = false) {
  let toReturn = `midas-element-${id}`;
  return includeSelector ? "#" + toReturn : toReturn;
}

declare global {
  interface Window { sidebar: MidasContainer; }
}

interface DeleteButtonProps {
  onClick: MouseEventHandler;
}

interface ContainerState {
  elements: ContainerElementState[];
}

interface ContainerElementState {
  id: number;
  name: string;
}

interface MidasElementProps {
  id: number;
  onClick: MouseEventHandler;
  name: string;
}

interface MidasElementState {
  hidden: boolean;
}

function DeleteButton(props: DeleteButtonProps): ReactElement {
  return (
    <button className="midas-header-button" onClick={props.onClick}>
      x
    </button>
  );
}


class MidasElement extends React.Component<MidasElementProps, MidasElementState> {
  constructor(props: any) {
    super(props);
    this.state = { hidden: false };
  }

  toggleHiddenStatus() {
    this.setState(prevState => {
      return { hidden: !prevState.hidden };
    });
  }

  render() {
    return (
      <div className="midas-element">
        <div className="midas-header">
          <span className="midas-title">{this.props.name}</span>
          <div className="midas-header-options"></div>
          <button
            className={"midas-header-button"}
            onClick={() => this.toggleHiddenStatus()}>
            {this.state.hidden ? "+" : "-"}
          </button>

          <DeleteButton onClick={this.props.onClick} />
        </div>
        <div
          id={makeElementId(this.props.id)}
          style={this.state.hidden ? { display: "none" } : {}}
        />
      </div>
    );
  }
}

class MidasContainer extends React.Component<any, ContainerState> {
  constructor(props?: any) {
    super(props);
    this.state = {
      elements: [],
    };
  }

  addDataFrame(key: number, dfName: string) {
    let shouldReturn = false;
    this.state.elements.forEach(({ name, id }) => {
      if (id === key) {
        shouldReturn = true;
      }
    });

    if (shouldReturn) return;

    let newElements = this.state.elements.concat([{
      id: key,
      name: dfName,
    }]);

    this.setState({ elements: newElements });
  }

  removeDataFrame(key: number) {
    this.setState(prevState => {
      return {
        elements: prevState.elements.filter(e => (e.id !== key))
      };
    });
  }

  render() {

    return (
      <div id="midas-floater-container">
            {this.state.elements.map(({ id, name }, index) => (
              <MidasElement id= { id } key = { id } name = { name } onClick = {() => this.removeDataFrame(id)} />
        ))}
      </div>
    );
  }
}

export function addDataFrame(id: number, df_name: string) {
  if (window.sidebar === undefined) {
    return;
  }
  window.sidebar.addDataFrame(id, df_name);
}

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

export function createFloater() {
  let floater = $("<div id=\"midas-floater-wrapper\"/>");
  let reactWrapper = $("<div id=\"midas-react-wrapper\">");

  makeResizer(floater);

  floater.append(reactWrapper);

  $("#notebook").append(floater);


  ReactDOM.render(<MidasContainer ref={(comp) => window.sidebar = comp} />, document.getElementById("midas-react-wrapper"));

  // $("#midas-floater-wrapper").css("position", "fixed");
  $("#midas-floating-container").height($("#midas-floater-wrapper").innerHeight);
}


