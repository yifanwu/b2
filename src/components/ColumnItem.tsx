/// <reference path="../external/Jupyter.d.ts" />

import React, { MouseEventHandler } from "react";
import { MIDAS_CELL_COMM_NAME } from "../constants";
// https://stackoverflow.com/questions/34126296/disable-jupyter-keyboard-shortcuts

interface ColumnItemProps {
  tableName: string;
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

    const c = Jupyter.notebook.insert_cell_above("code");
    const date = new Date().toLocaleString("en-US");

    let newDfName = `${this.props.tableName}_${this.props.columnName}`

    const text = `# [MIDAS] You selected the following projection on ${this.props.tableName} at time ${date}\n${newDfName} = ${this.props.tableName}.select(['${this.props.columnName}'])`
    c.set_text(text);
    c.execute();

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

