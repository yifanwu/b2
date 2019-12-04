import React from "react";
import MidasContainer from "./MidasContainer";
import { SelectionShelf } from "./SelectionShelf";
import { ProfilerShelf } from "./ProfilerShelf";
import CellManager from "../CellManager";

interface MidasSidebarProps {
  comm: any;
  cellManager: CellManager;
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
    const midbar = (
      <div id="midas-midbar">
        <ProfilerShelf
          ref={this.setProfilerShelfRef}
          comm={this.props.comm}
        />
        <SelectionShelf
          ref={this.setSelectionShelfRef}
          comm={this.props.comm}
          cellManager={this.props.cellManager}
        />
    </div>);
    const displayStyle = this.state.isShown ? "block" : "none";
    return (
      <div style={{ "display": displayStyle }}>
        <div id="midas-resizer"></div>
        <div className="midas-inside">
          { midbar }
          <MidasContainer
            comm={this.props.comm}
            cellManager={this.props.cellManager}
            ref={this.setMidasContainerRef}/>
        </div>
      </div>
    );
  }
}
