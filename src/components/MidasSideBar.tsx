import React, {RefObject} from "react"; 
import MidasContainer from "./MidasContainer";
import MidasMidbar from "./MidasMidbar";
import {SelectionShelf} from "./SelectionShelf";
import {ColumnShelf} from "./ColumnShelf";

export class MidasSideBar extends React.Component<{}, {}> {

  midasContainerRef: MidasContainer;
  selectionShelfRef: SelectionShelf;
  columnShelfRef: ColumnShelf;

  constructor(props?: {}) {
    super(props);

    this.setMidasContainerRef = this.setMidasContainerRef.bind(this);
    this.setColumnShelfRef = this.setColumnShelfRef.bind(this);
    this.setSelectionShelfRef = this.setSelectionShelfRef.bind(this);
  }

  setMidasContainerRef(input: MidasContainer) {
    this.midasContainerRef = input;
  }

  setColumnShelfRef(input: ColumnShelf) {
    this.columnShelfRef = input;
  }


  setSelectionShelfRef(input: SelectionShelf) {
    this.selectionShelfRef = input;
  }


  getMidasContainerRef() {
    return this.midasContainerRef;
  }

  getColumnShelfRef() {
    return this.columnShelfRef;
  }

  getSelectionShelfRef() {
    return this.selectionShelfRef;
  }


    render() {
      let midbar = (
        <div id="midas-midbar">
        <div>
          <h1 className="midbar-shelf-header">
            Column Shelf
            </h1>
            <ColumnShelf ref={this.setColumnShelfRef}/>
          </div>
        <div>
          <h1 className="midbar-shelf-header">
            Selection Shelf
          </h1>
          <SelectionShelf ref={this.setSelectionShelfRef}/>
        </div>
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
