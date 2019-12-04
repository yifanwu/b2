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
}

export class SelectionShelf extends React.Component<SelectionShelfProps, SelectionShelfState> {
  constructor(props: SelectionShelfProps) {
    super(props);
    this.setCurrentSelections = this.setCurrentSelections.bind(this);

    this.state = {
      selectionItem: [],
    };
  }

  addSelectionItem(selection: string) {
    this.setState(prevState => {
      prevState.selectionItem.push({
        title: `selection_${prevState.selectionItem.length}`,
        value: selection
      });
      return prevState;
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
    const content = (selectionDivs.length > 0) ? selectionDivs : <SelectionShelfLandingPage/>;
    const buttons = <>
    <button className="reset-button" onClick={this.resetAllSelection}>reset</button>
    </>;
    return <div className="shelf" id="selection-shelf">
      {buttons}
      {content}
      </div>;
  }
}

