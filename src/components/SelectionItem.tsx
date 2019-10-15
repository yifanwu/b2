/// <reference path="../external/Jupyter.d.ts" />

import React, { MouseEventHandler } from "react";
import {EditableText} from "./EditableText";
import {MIDAS_CELL_COMM_NAME} from "../constants";

interface SelectionItemState {
  selectionName: string;
}

interface SelectionItemProps {
  selectionName: string;
  onDelete: Function;
}

export class SelectionItem extends React.Component<SelectionItemProps, SelectionItemState> {
  constructor(props: SelectionItemProps) {
    super(props);
    this.state = {
      selectionName: this.props.selectionName,
    };
  }

  onSave(val: string) {
    Jupyter.keyboard_manager.enable();
    const prevName = this.state.selectionName;
    // TODO: somehow use prevstate for this? But can't seem to access in callback...
    this.setState({selectionName: val}, () => {
      const execute = `m.js_update_selection_shelf_selection_name('${prevName}', '${val}')`;
      console.log("clicked, and executing", execute);
      IPython.notebook.kernel.execute(execute);
    });
  }

  deleteButtonClicked() {
    const selName = this.state.selectionName;
    const execute = `m.js_remove_selection_from_shelf('${selName}')`;
    console.log("clicked, and executing", execute);
    IPython.notebook.kernel.execute(execute);
    this.props.onDelete();
 }

  clicked() {
    const comm = Jupyter.notebook.kernel.comm_manager.new_comm(MIDAS_CELL_COMM_NAME);
    const payload = {type: "name", value: this.state.selectionName};
    console.log(`Clicked, and sending message with contents ${JSON.stringify(payload)}`);
    comm.send(payload);

  }

  render() {
    return (
      <div className="midas-shelf-selection-item">
          <EditableText
            value={this.state.selectionName}
            onSave={(val) => this.onSave(val)}
            onDeleteButtonClicked={() => this.deleteButtonClicked()}
            onTextClicked={() => this.clicked()}
            onEditStart={() => Jupyter.keyboard_manager.disable()}
          />
      </div>
    );
  }
}

