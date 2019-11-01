import React from "react";
import { SelectionItem } from "./SelectionItem";

interface SelectionShelfState {
  selectionItemTitles: string[];
}

export class SelectionShelf extends React.Component<{}, SelectionShelfState> {
  constructor(props?: {}) {
    super(props);
    this.state = {
      selectionItemTitles: [],
    };
  }

  addSelectionItem(title: string) {
    this.setState(prevState => {
      prevState.selectionItemTitles.push(title);
      return prevState;
    });
  }

  deleteItem(index: number) {
    this.setState(prevState => {
      console.log(prevState.selectionItemTitles);
      prevState.selectionItemTitles.splice(index, 1);
      console.log(index);
      console.log(prevState.selectionItemTitles);
      return prevState;
    });
  }

  render() {
    return (
      <>
      {this.state.selectionItemTitles.map(
        (selectionName, index) => <SelectionItem selectionName={selectionName}
              onDelete={() => this.deleteItem(index)} key={selectionName}/>)}
      </>
    );
  }

}

