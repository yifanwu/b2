import React from "react";
import MidasContainer from "./MidasContainer";
import { SelectionShelf } from "./SelectionShelf";
import { ProfilerShelf } from "./ProfilerShelf";

interface MidasSidebarState {
  isShown: boolean;
}

export class MidasSidebar extends React.Component<{}, {}> {

  midasContainerRef: MidasContainer;
  selectionShelfRef: SelectionShelf;
  profilerShelfRef: ProfilerShelf;

  constructor(props?: {}) {
    super(props);
    this.state = {
      isShown: true
    };

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

  set_comm(comm: any) {
    this.midasContainerRef.setComm(comm);
  }

  render() {
    const midbar = (
      <div id="midas-midbar">
        <ProfilerShelf ref={this.setProfilerShelfRef}/>
        <SelectionShelf ref={this.setSelectionShelfRef}/>
    </div>);
  return (
    <div style={{this.state.isShown ? "block" : "none"}}>
      <div id="midas-resizer"></div>
      <div className="midas-inside">
        { midbar }
        <MidasContainer ref={this.setMidasContainerRef}></MidasContainer>
      </div>
    </div>
  );
  }
}
