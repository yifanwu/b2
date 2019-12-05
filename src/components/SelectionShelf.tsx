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
  currentActiveSelection: number;
}

export class SelectionShelf extends React.Component<SelectionShelfProps, SelectionShelfState> {
  constructor(props: SelectionShelfProps) {
    super(props);
    this.setCurrentSelections = this.setCurrentSelections.bind(this);

    this.state = {
      selectionItem: [],
      currentActiveSelection: 0,
      resetDisabled: true
    };
  }

  addSelectionItem(selection: string) {
    this.setState(prevState => {
      const selectionItem = prevState.selectionItem;
      const resetDisabled = (selection === "") ? true : false;
      const idx = prevState.selectionItem.findIndex(s => s.value === selection);
      if (idx > -1) {
        const currentActiveSelection = idx;
        return { selectionItem , resetDisabled, currentActiveSelection };
      }
      else {
        const l = prevState.selectionItem.length;
        prevState.selectionItem.push({
          title: `snapNo${l + 1}`,
          value: selection
        });
        const currentActiveSelection = l;
        return { selectionItem, resetDisabled, currentActiveSelection };
      }
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
    this.props.cellManager.makeSelectionFromCharts(this.state.selectionItem[index].value);
  }

  resetAllSelection() {
    this.props.cellManager.makeSelectionFromCharts("");
  }

  render() {
    const selectionDivs = this.state.selectionItem.map(
      (selection, index) => <SelectionItem
        isActive={index === this.state.currentActiveSelection}
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

