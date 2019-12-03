import React from "react";
import { SelectionItem } from "./SelectionItem";
import { SelectionShelfLandingPage } from "./SelectionShelfLandingPage";

interface SelectionShelfState {
  selectionItemTitles: string[];
}

interface SelectionShelfProps {
  comm: any;
}


export class SelectionShelf extends React.Component<SelectionShelfProps, SelectionShelfState> {
  constructor(props: SelectionShelfProps) {
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
    const selectionDivs = this.state.selectionItemTitles.map(
      (selectionName, index) => <SelectionItem selectionName={selectionName}
            onDelete={() => this.deleteItem(index)} key={selectionName}/>);
    const content = (selectionDivs.length > 0) ? selectionDivs : <SelectionShelfLandingPage/>;
    return <div className="shelf" id="selection-shelf">
      {content}
      </div>;
  }
}

