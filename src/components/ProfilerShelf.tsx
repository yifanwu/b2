import React from "react";

import { ColumnItem } from "./ColumnItem";
import { ProfileShelfLandingPage } from "./ProfileShelfLandingPage";
import { LogDebug, addNotebookMenuBtn } from "../utils";
import { TOGGLE_PANE_BUTTON } from "../constants";
import { LoggerFunction, LogEntryBase } from "../logging";

interface ProfilerColumn {
  columnName: string;
  columnType: string;
  hasSeen?: boolean;
  hasError?: boolean;
}

interface ProfilerShelfState {
  tables: { [index: string]: ProfilerColumn[] };
  isShown: { [index: string]: boolean; };
  isShownAll: boolean;
}

interface ProfilerShelfProps {
  columnSelectMsg: (columnName: string, tableName: string) => void;
  logger: LoggerFunction;
}

export class ProfilerShelf extends React.Component<ProfilerShelfProps, ProfilerShelfState> {
  constructor(props: ProfilerShelfProps) {
    super(props);
    this.columnClicked  = this.columnClicked.bind(this);
    this.toggleTable = this.toggleTable.bind(this);
    this.togglePane = this.togglePane.bind(this);
    this.markAsSeen = this.markAsSeen.bind(this);

    addNotebookMenuBtn(this.togglePane, TOGGLE_PANE_BUTTON, "Toggle Columns", "Toggle the yellow column pane");
    this.state = {
      tables: {},
      isShown: {},
      isShownAll: true,
    };
  }


  addOrReplaceTableItem(tableName: string, columnItems: ProfilerColumn[], cellId: number) {
    // just do nothing with the cellId for now
    this.setState(prevState => {
      prevState.tables[tableName] = columnItems;
      prevState.isShown[tableName] = true;
      return prevState;
    });
  }

  columnClicked(columnName: string, tableName: string) {
    this.props.columnSelectMsg(columnName, tableName);
    this.markAsSeen(columnName, tableName);
  }

  markAsErrored(columnName: string, tableName: string) {
    this.setState(prevState => {
      const idx = prevState.tables[tableName].findIndex((i) => i.columnName === columnName);
      prevState.tables[tableName][idx].hasError = true;
      return prevState;
    });
  }

  markAsSeen(columnName: string, tableName: string) {
    this.setState(prevState => {
      const idx = prevState.tables[tableName].findIndex((i) => i.columnName === columnName);
      prevState.tables[tableName][idx].hasSeen = true;
      return prevState;
    });
  }

  hideItem(tableName: string, index: number) {
    if (confirm("are you sure you want to hide the column?")) {
      this.setState(prevState => {
        prevState.tables[tableName].splice(index, 1);
        return prevState;
      });
    }
  }

  togglePane() {
    this.setState(prevState => {
      const action = prevState.isShownAll
        ? "hide_columns_pane"
        : "show_columns_pane";
      const entry: LogEntryBase = {
        action,
        actionKind: "ui_control",
      };
      this.props.logger(entry);
      return { isShownAll: !prevState.isShownAll};
    });
  }

  toggleTable(tableName: string) {
    return () => {
      LogDebug("toggle view", tableName);
      this.setState(prevState => {
        prevState.isShown[tableName] = !prevState.isShown[tableName];
        return prevState;
      });
    };
  }

  // dragEnd(event: any) {
  //   const currentX = event.clientX;
  //   const currentY = event.clientY;
  //   this.setState(prevState => {
  //     const x = (currentX - prevState.oldX) + prevState.x;
  //     const y = (currentY - prevState.oldY) + prevState.y;
  //     LogDebug(`DragEnd positions: ${currentX}, ${currentY}, ${prevState.oldX}, ${prevState.oldY}, with new values ${x}, ${y}]`);
  //     return {
  //       x,
  //       y,
  //       dragged: true
  //     };
  //   });
  //   event.preventDefault();
  // }

  // dragStart(event: any) {
  //   const oldX = event.clientX;
  //   const oldY = event.clientY;
  //   LogDebug(`DragStart positions: ${oldX}, ${oldY}`);
  //   this.setState({
  //     oldX,
  //     oldY
  //   });
  // }

  render() {
    const tableDivs = Object.keys(this.state.tables).map((tableName) => {
      const columns = this.state.isShown[tableName]
        ? this.state.tables[tableName].map((c, i) => <ColumnItem
          key={`column-${tableName}-${c.columnName}`}
          tableName={tableName}
          columnName={c.columnName}
          columnType={c.columnType}
          onClick={() => this.columnClicked(c.columnName, tableName)}
          onDelete={() => this.hideItem(tableName, i)}
          hasSeen={c.hasSeen}
          hasError={c.hasError}
        />)
        : [];
      return <div className="profiler-table" key={`table-${tableName}`}>
        <div className="profiler-table-name" onClick={this.toggleTable(tableName)}>{tableName}</div>
        {columns}
      </div>;
    });
    const content = (tableDivs.length > 0)
      ? tableDivs.reverse()
      : <ProfileShelfLandingPage/>
      ;
    // const style = {left: this.state.x, top: this.state.y};
    const style = this.state.isShownAll
      ? {}
      : {"display": "none"}
      ;
    return (
      <div
        className="shelf"
        id="profiler-shelf"
        style={style}
        // ok this dragging thing is annoying
        // draggable={true}
        // onDragStart={this.dragStart}
        // onDragOver={(event) => event.preventDefault()}
        // onDragEnd={this.dragEnd}
        // style={style}
      >
      {content}
      </div>
    );
  }
}
