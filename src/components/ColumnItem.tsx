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
    const payload = {
      command: "column-selected",
      column: this.props.columnName,
      df_name: this.props.tableName,
    };
    console.log(`Clicked, and sending message with contents ${JSON.stringify(payload)}`);
    comm.send(payload);
  }

  render() {
    return (
      <div className="midas-shelf-selection-item">
        <div className="column-item-header">
          <span className="selection-column-name" onClick={() => this.clicked()}>{this.props.columnName}</span>
          {/* <button className="midas-header-button" onClick={() => this.props.onDelete()}>x</button> */}
          <CloseButton onClick={this.props.onDelete} size={10}/>
        </div>
      </div>
    );
  }
}

