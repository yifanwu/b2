import React, { MouseEventHandler } from "react";
import {ColumnItem} from "./ColumnItem"

interface Column {
  columnName: string;
  columnType: string;
}

interface ColumnShelfState {
  columnItems: Column[];
}

export class ColumnShelf extends React.Component<{}, ColumnShelfState> {
  constructor(props?: {}) {
    super(props);
    this.state = {
      columnItems: [],
    };
  }

  addColumnItem(columnName: string, type: string) {
    this.setState(prevState => {
      prevState.columnItems.push({
        columnName: columnName,
        columnType: type,
      });
      return prevState;
    });
  }

  deleteItem(index: number) {
    this.setState(prevState => {
      prevState.columnItems.splice(index, 1);
      return prevState;
    });
  }

  render() {
    return (
      <>
      {this.state.columnItems.map(
        ({columnName, columnType}, index) =>
        <ColumnItem columnName={columnName}
              columnType={columnType}
              onDelete={() => this.deleteItem(index)}/>)}
      </>
    );
  }

}

