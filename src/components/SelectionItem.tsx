/// <reference path="../external/Jupyter.d.ts" />

import React from "react";
import { EditableText } from "./EditableText";


interface SelectionItemProps {
  isActive: boolean;
  selectionName: string;
  onDelete: () => void;
  onClick: () => void;
}

interface SelectionItemState {
  selectionName: string;
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


  render() {
    return (
      <div className={`midas-shelf-selection-item`}>
          <EditableText
            isActive={this.props.isActive}
            value={this.state.selectionName}
            onSave={(val) => this.onSave(val)}
            onDeleteButtonClicked={this.props.onDelete}
            onTextClicked={this.props.onClick}
            onEditStart={() => Jupyter.keyboard_manager.disable()}
          />
      </div>
    );
  }
}
