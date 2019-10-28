import * as React from "react";
interface EditableTextState {
  editing: boolean; // True if currently editing
  savedValue: string; // The value most recently saved
  temporaryValue: string; // The current value being typed in
}

interface EditableTextProps {
  value: string;
  onSave: (newValue: string) => void;
  onTextClicked: (event: React.MouseEvent<HTMLDivElement, MouseEvent>) => void;
  onDeleteButtonClicked: () => void;
  onEditStart: () => void;
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
      return (
        <div className="editable-text-header">
          <span className="editable-text-title" onClick={this.props.onTextClicked}> {this.state.savedValue} </span>
          <button className="editable-text-button" onClick={() => this.startEditing()}>Edit</button>
          <button className="editable-text-button" onClick={() => this.props.onDeleteButtonClicked()}>x</button>
        </div>
      );
    }
  }
}
