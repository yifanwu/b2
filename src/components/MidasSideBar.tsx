import React from "react"; 
import MidasContainer from "./MidasContainer";
import { SelectionShelf } from "./SelectionShelf";
import { ProfilerShelf } from "./ProfilerShelf";

export class MidasSidebar extends React.Component<{}, {}> {

  midasContainerRef: MidasContainer;
  selectionShelfRef: SelectionShelf;
  profilerShelfRef: ProfilerShelf;

  constructor(props?: {}) {
    super(props);

    this.setMidasContainerRef = this.setMidasContainerRef.bind(this);
    this.setProfilerShelfRef = this.setProfilerShelfRef.bind(this);
    this.setSelectionShelfRef = this.setSelectionShelfRef.bind(this);
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
    this.midasContainerRef.set_comm(comm);
  }

  render() {
    let midbar = (
      <div id="midas-midbar">
        <ProfilerShelf ref={this.setProfilerShelfRef}/>
        <SelectionShelf ref={this.setSelectionShelfRef}/>
    </div>
    )
  return (
    <>
    <div id="midas-resizer"></div>

    <div className="midas-inside">
      {midbar}
      <MidasContainer ref={this.setMidasContainerRef}></MidasContainer>
    </div>
    </>
  );
  }
}
