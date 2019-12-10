import React from "react";
import MidasContainer from "./MidasContainer";
import { SelectionShelf } from "./SelectionShelf";
import { ProfilerShelf } from "./ProfilerShelf";
import CellManager from "../CellManager";

interface MidasSidebarProps {
  columnSelectMsg: (col: string, table: string) => void;
  addCurrentSelectionMsg: (valueStr: string) => void;
  makeSelectionFromShelf: (selection: string) => void;
}

interface MidasSidebarState {
  isShown: boolean;
}

export class MidasSidebar extends React.Component<MidasSidebarProps, MidasSidebarState> {

  midasContainerRef: MidasContainer;
  selectionShelfRef: SelectionShelf;
  profilerShelfRef: ProfilerShelf;

  constructor(props?: MidasSidebarProps) {
    super(props);
    this.state = {
      isShown: true
    };

    this.hide = this.hide.bind(this);
    this.show = this.show.bind(this);

    this.setMidasContainerRef = this.setMidasContainerRef.bind(this);
    this.setProfilerShelfRef = this.setProfilerShelfRef.bind(this);
    this.setSelectionShelfRef = this.setSelectionShelfRef.bind(this);
  }

  hide() {
    this.setState({ isShown: false });
  }
  show() {
    this.setState({ isShown: true });
  }

  setMidasContainerRef(input: MidasContainer) {
    this.midasContainerRef = input;
  }

  setProfilerShelfRef(input: ProfilerShelf) {
    this.profilerShelfRef = input;
  }

  setSelectionShelfRef(input: SelectionShelf) {
    this.selectionShelfRef = input;
  }

  getMidasContainerRef() {
    return this.midasContainerRef;
  }

  getProfilerShelfRef() {
    return this.profilerShelfRef;
  }

  getSelectionShelfRef() {
    return this.selectionShelfRef;
  }

  render() {
    if (!this.state.isShown) {
      return <></>;
    }
    const midbar = (
      <div id="midas-midbar">
        <ProfilerShelf
          ref={this.setProfilerShelfRef}
          columnSelectMsg={this.props.columnSelectMsg}
        />
        <SelectionShelf
          ref={this.setSelectionShelfRef}
          makeSelectionFromShelf={this.props.makeSelectionFromShelf}
        />
    </div>);
    return (<>
        <div id="midas-resizer"></div>
        <div className="midas-inside">
          { midbar }
          <MidasContainer
            addCurrentSelectionMsg={this.props.addCurrentSelectionMsg}
            ref={this.setMidasContainerRef}/>
        </div></>
    );
  }
}
