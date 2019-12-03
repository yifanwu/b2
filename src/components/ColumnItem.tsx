/// <reference path="../external/Jupyter.d.ts" />

import React, { MouseEventHandler } from "react";
import { SHELF_TEXT_MAX_LEN } from "../constants";
import { CloseButton } from "./CloseButton";
import { trimStr } from "./../utils";
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
    const shownName = trimStr(this.props.columnName, SHELF_TEXT_MAX_LEN);
    return (
      <div className="midas-shelf-selection-item">
        <div className="column-item-header">
        <span
          className="selection-column-name"
          onClick={this.props.onClick}
          title={this.props.columnName}
        >{shownName}</span>
          <CloseButton onClick={this.props.onDelete} size={10}/>
        </div>
      </div>
    );
  }
}

