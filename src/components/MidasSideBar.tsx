import React from "react";
import MidasContainer from "./MidasContainer";
import { SelectionShelf } from "./SelectionShelf";
import { ProfilerShelf } from "./ProfilerShelf";
import { MidasContainerFunctions } from "../types";
import { TOGGLE_MIDAS_BUTTON } from "../constants";

interface MidasSidebarProps {
  columnSelectMsg: (col: string, table: string) => void;
  // makeSelectionFromShelf: (selection: string) => void;
  midasElementFunctions: MidasContainerFunctions;
}

interface MidasSidebarState {
  isShown: boolean;
  curWidth: number;
}

function createToggleAllButton(clickFn: () => void) {
  if (!$(`#${TOGGLE_MIDAS_BUTTON}`).length) {
    // create if does not exist
    const newButton = `<div class="btn-group">
      <button
        id="${TOGGLE_MIDAS_BUTTON}"
        class="btn btn-default one-time-animation"
        title="Take a snapshot of current charts"
      >Toggle Midas</button>
    </div>`;
    $("#maintoolbar-container").append(newButton);
  }
  $(`#${TOGGLE_MIDAS_BUTTON}`).click(() => clickFn());
  return;
}


export class MidasSidebar extends React.Component<MidasSidebarProps, MidasSidebarState> {

  midasContainerRef: MidasContainer;
  // selectionShelfRef: SelectionShelf;
  profilerShelfRef: ProfilerShelf;
  constructor(props?: MidasSidebarProps) {
    super(props);
    this.state = {
      isShown: true,
      curWidth: 758,
    };

    this.toggle = this.toggle.bind(this);
    createToggleAllButton(this.toggle);

    this.setMidasContainerRef = this.setMidasContainerRef.bind(this);
    this.setProfilerShelfRef = this.setProfilerShelfRef.bind(this);
    // this.setSelectionShelfRef = this.setSelectionShelfRef.bind(this);
  }

  toggle() {
    this.setState(prevState => {
      if (prevState.isShown) {
        const curWidth = $("#midas-sidebar-wrapper").width();
        return {
          isShown: !prevState.isShown,
          curWidth
        };
      } else {
        return {
          isShown: !prevState.isShown,
          curWidth: prevState.curWidth
        };
      }
    });
  }

  setMidasContainerRef(input: MidasContainer) {
    this.midasContainerRef = input;
  }

  setProfilerShelfRef(input: ProfilerShelf) {
    this.profilerShelfRef = input;
  }

  // setSelectionShelfRef(input: SelectionShelf) {
  //   this.selectionShelfRef = input;
  // }

  getMidasContainerRef() {
    return this.midasContainerRef;
  }

  getProfilerShelfRef() {
    return this.profilerShelfRef;
  }

  // getSelectionShelfRef() {
  //   return this.selectionShelfRef;
  // }

  render() {
    if (!this.state.isShown) {
      $("#midas-sidebar-wrapper").width(10);
    } else {
      $("#midas-sidebar-wrapper").width(this.state.curWidth);
    }
    return (<>
        <div id="midas-resizer"></div>
        <div id="midas-inside">
          <MidasContainer
            containerFunctions={this.props.midasElementFunctions}
            ref={this.setMidasContainerRef}/>
          <ProfilerShelf
            ref={this.setProfilerShelfRef}
            columnSelectMsg={this.props.columnSelectMsg}
          />
        </div></>
    );
  }
}
