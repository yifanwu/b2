import React, { MouseEventHandler } from "react";
import {SelectionItem} from "./SelectionItem";
import { key } from "vega";

interface SelectionShelfState {
  selectionItemNames: string[];
}

export class SelectionShelf extends React.Component<{}, SelectionShelfState> {
  constructor(props?: {}) {
    super(props);
    this.state = {
      selectionItemNames: [],
    };
  }

  addSelectionItem(name: string) {
    this.setState(prevState => {
      prevState.selectionItemNames.push(name);
      return prevState;
    });
  }

  deleteItem(index: number) {
    this.setState(prevState => {
      console.log(prevState.selectionItemNames);
      prevState.selectionItemNames.splice(index, 1);
      console.log(index);
      console.log(prevState.selectionItemNames);
      return prevState;
    });
  }

  render() {
    return (
      <>
      {this.state.selectionItemNames.map(
        (selectionName, index) => <SelectionItem selectionName={selectionName}
              onDelete={() => this.deleteItem(index)} key={selectionName}/>)}
      </>
    );
  }

}

