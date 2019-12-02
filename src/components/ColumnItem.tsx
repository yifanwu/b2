/// <reference path="../external/Jupyter.d.ts" />

import React, { MouseEventHandler } from "react";
import { MIDAS_CELL_COMM_NAME } from "../constants";
import { CloseButton } from "./CloseButton";
// https://stackoverflow.com/questions/34126296/disable-jupyter-keyboard-shortcuts

interface ColumnItemProps {
  tableName: string;
  columnName: string;
  columnType: string;
  onDelete: () => void;
  onClick: () => void;
}

export class ColumnItem extends React.Component<ColumnItemProps, {}> {
  constructor(props: ColumnItemProps) {
    super(props);
    this.state = {
      columnName: this.props.columnName,
    };
  }

  render() {
    return (
      <div className="midas-shelf-selection-item">
        <div className="column-item-header">
          <span className="selection-column-name" onClick={this.props.onClick}>{this.props.columnName}</span>
          <CloseButton onClick={this.props.onDelete} size={10}/>
        </div>
      </div>
    );
  }
}

