/// <reference path="../external/Jupyter.d.ts" />

import React, { MouseEventHandler } from "react";
import {MIDAS_CELL_COMM_NAME} from "../constants";
// https://stackoverflow.com/questions/34126296/disable-jupyter-keyboard-shortcuts

interface ColumnItemProps {
  columnName: string;
  columnType: string;
  onDelete: Function;
}

export class ColumnItem extends React.Component<ColumnItemProps, {}> {
  constructor(props: ColumnItemProps) {
    super(props);
    this.state = {
      columnName: this.props.columnName,
    };
  }

  clicked() {
    const comm = Jupyter.notebook.kernel.comm_manager.new_comm(MIDAS_CELL_COMM_NAME);
    const payload = {type: "column-name", value: this.props.columnName};
    console.log(`Clicked, and sending message with contents ${JSON.stringify(payload)}`);
    comm.send(payload);

  }

  render() {
    return (
      <div className="midas-shelf-selection-item">
        <div className="column-item-header">
          <span className="selection-column-name" onClick={() => this.clicked()}>{this.props.columnName}</span>
          <button className="midas-header-button" onClick={() => this.props.onDelete()}>x</button>
        </div>
      </div>
    );
  }
}

