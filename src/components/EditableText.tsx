import * as React from "react";
import { CloseButton } from "./CloseButton";
import { trimStr } from "./../utils";
import { SELECTION_TEXT_MAX_LEN } from "./../constants";

interface EditableTextProps {
  isActive: boolean;
  value: string;
  onSave: (newValue: string) => void;
  onTextClicked: (event: React.MouseEvent<HTMLDivElement, MouseEvent>) => void;
  onDeleteButtonClicked: () => void;
  onEditStart: () => void;
}

interface EditableTextState {
  editing: boolean; // True if currently editing
  savedValue: string; // The value most recently saved
  temporaryValue: string; // The current value being typed in
}


export class EditableText extends React.Component<EditableTextProps, EditableTextState> {
  constructor(props: EditableTextProps) {
    super(props);
    this.state = {
      editing: false,
      savedValue: props.value,
      temporaryValue: "",
    };
  }

  handleInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    this.setState({
      temporaryValue: e.target.value,
      savedValue: this.state.savedValue,
      editing: true,
    });
  }

  startEditing() {
    this.props.onEditStart();
    this.setState({
      temporaryValue: this.state.savedValue,
      savedValue: this.state.savedValue,
      editing: true,
    });
  }

  stopEditingAndSave() {
    this.setState(prevState => ({
        temporaryValue: "",
        savedValue: prevState.temporaryValue,
        editing: false,
      }
    ), () => {
      this.props.onSave(this.state.savedValue);
    });
  }

  render() {
    if (this.state.editing) {
      return (
        <div className="editable-text-header">
          <input value={this.state.temporaryValue}
                 onChange={e => this.handleInputChange(e)}
                 autoFocus={this.state.editing}
                 className="editable-text-title"
          />
          <button className="editable-text-button" onClick={() => this.stopEditingAndSave()}>Done</button>
        </div>
      );
    } else {

      const additionalClass = this.props.isActive ? "active-selection-item" : "";
      const savedValue = this.state.savedValue;
      const shownName = trimStr(savedValue, SELECTION_TEXT_MAX_LEN);
      const textDiv = (shownName.length < this.state.savedValue.length)
        ? <a className="tip">{shownName}<span>{savedValue}</span></a>
        : <span>{savedValue}</span>;
      return (
        <div className={`shelf-item editable-text-header ${additionalClass}`}>
          <span className="editable-text-title" onClick={this.props.onTextClicked}>
            {textDiv}
          </span>
          <a onClick={() => this.startEditing()}> ✏️</a>
          <CloseButton onClick={this.props.onDeleteButtonClicked} size={10}/>
        </div>
      );
    }
  }
}
