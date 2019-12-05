import React from "react";
import { SelectionItem } from "./SelectionItem";
import { SelectionShelfLandingPage } from "./SelectionShelfLandingPage";
import CellManager from "../CellManager";

interface SelectionShelfProps {
  comm: any;
  cellManager: CellManager;
}

interface SelectionShelfState {
  selectionItem: {title: string, value: string}[];
  resetDisabled: boolean;
}

export class SelectionShelf extends React.Component<SelectionShelfProps, SelectionShelfState> {
  constructor(props: SelectionShelfProps) {
    super(props);
    this.setCurrentSelections = this.setCurrentSelections.bind(this);

    this.state = {
      selectionItem: [],
      resetDisabled: true
    };
  }

  addSelectionItem(selection: string) {
    // also if selection is empty string, ""
    //   then we disable the reset-button, otherwise enable it
    this.setState(prevState => {
      prevState.selectionItem.push({
        title: `snapNo${prevState.selectionItem.length + 1}`,
        value: selection
      });
      const selectionItem = prevState.selectionItem;
      const resetDisabled = (selection === "") ? true : false;
      return { selectionItem, resetDisabled };
    });
  }

  deleteItem(index: number) {
    this.setState(prevState => {
      console.log(prevState.selectionItem);
      prevState.selectionItem.splice(index, 1);
      console.log(index);
      console.log(prevState.selectionItem);
      return prevState;
    });
  }


  setCurrentSelections(index: number) {
    // here we add to the cell state directly
    this.props.cellManager.makeSelection(this.state.selectionItem[index].value);
  }

  resetAllSelection() {
    this.props.cellManager.makeSelection("");
  }

  render() {
    const selectionDivs = this.state.selectionItem.map(
      (selection, index) => <SelectionItem
        selectionName={selection.title}
        onDelete={() => this.deleteItem(index)}
        onClick={() => this.setCurrentSelections(index)}
        key={selection.title}
      />);
    const selectedContent = <div>
      <button className="reset-button" disabled={this.state.resetDisabled} onClick={this.resetAllSelection}>reset</button>
      {selectionDivs}
    </div>;
    const content = (selectionDivs.length > 0) ? selectedContent : <SelectionShelfLandingPage/>;
    return <div className="shelf" id="selection-shelf">
      {content}
      </div>;
  }
}

