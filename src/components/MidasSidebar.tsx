import React from "react";
import MidasContainer from "./MidasContainer";
import { ProfilerShelf } from "./ProfilerShelf";
import { MidasContainerFunctions } from "../types";
import { TOGGLE_MIDAS_BUTTON } from "../constants";
import { addNotebookMenuBtn } from "../utils";
import { LogEntryBase } from "../logging";

interface MidasSidebarProps {
  columnSelectMsg: (col: string, table: string) => void;
  // makeSelectionFromShelf: (selection: string) => void;
  midasElementFunctions: MidasContainerFunctions;
}

interface MidasSidebarState {
  isShown: boolean;
  curWidth: number;
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
    addNotebookMenuBtn(this.toggle, TOGGLE_MIDAS_BUTTON, "Toggle Midas", "Toggle the Midas pane");

    this.setMidasContainerRef = this.setMidasContainerRef.bind(this);
    this.setProfilerShelfRef = this.setProfilerShelfRef.bind(this);
  }

  toggle() {
    this.setState(prevState => {
      const action = prevState.isShown
        ? "hide_midas"
        : "show_midas"
        ;
      const entry: LogEntryBase = {
        action,
        actionKind: "ui_control",
      };
      this.props.midasElementFunctions.elementFunctions.logger(entry);
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
            logger={this.props.midasElementFunctions.elementFunctions.logger}
          />
        </div></>
    );
  }
}
