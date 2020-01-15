import React from "react";

import { ColumnItem } from "./ColumnItem";
import { ProfileShelfLandingPage } from "./ProfileShelfLandingPage";
import { LogDebug } from "../utils";

interface ProfilerColumn {
  columnName: string;
  columnType: string;
}

interface ProfilerShelfState {
  tables: { [index: string]: ProfilerColumn[] };
  isShown: { [index: string]: boolean; };
  dragged: boolean;
  oldX: number;
  oldY: number;
  x: number;
  y: number;
}

interface ProfilerShelfProps {
  columnSelectMsg: (columnName: string, tableName: string) => void;
}

export class ProfilerShelf extends React.Component<ProfilerShelfProps, ProfilerShelfState> {
  constructor(props: ProfilerShelfProps) {
    super(props);
    this.columnClicked  = this.columnClicked.bind(this);
    this.toggleView = this.toggleView.bind(this);
    // this.drop = this.drop.bind(this);
    this.dragEnd = this.dragEnd.bind(this);
    this.dragStart = this.dragStart.bind(this);
    this.state = {
      tables: {},
      isShown: {},
      dragged: false,
      oldX: 0,
      oldY: 0,
      x: 0,
      y: 0,
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
  }

  hideItem(tableName: string, index: number) {
    this.setState(prevState => {
      prevState.tables[tableName].splice(index, 1);
      return prevState;
    });
  }

  toggleView(tableName: string) {
    return () => {
      LogDebug("toggle view", tableName);
      this.setState(prevState => {
        prevState.isShown[tableName] = !prevState.isShown[tableName];
        return prevState;
      });
    };
  }

  dragEnd(event: any) {
    const currentX = event.clientX;
    const currentY = event.clientY;
    this.setState(prevState => {
      const x = (currentX - prevState.oldX) + prevState.x;
      const y = (currentY - prevState.oldY) + prevState.y;
      LogDebug(`DragEnd positions: ${currentX}, ${currentY}, ${prevState.oldX}, ${prevState.oldY}, with new values ${x}, ${y}]`);
      return {
        x,
        y,
        dragged: true
      };
    });
    event.preventDefault();
  }

  dragStart(event: any) {
    const oldX = event.clientX;
    const oldY = event.clientY;
    LogDebug(`DragStart positions: ${oldX}, ${oldY}`);
    this.setState({
      oldX,
      oldY
    });
  }

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
        />)
        : [];
      return <div className="profiler-table" key={`table-${tableName}`}>
        <div className="profiler-table-name" onClick={this.toggleView(tableName)}>{tableName}</div>
        {columns}
      </div>;
    });
    const content = (tableDivs.length > 0) ? tableDivs : <ProfileShelfLandingPage/>;
    const style = {left: this.state.x, top: this.state.y};
    return (
      <div
        id="profiler-shelf"
        draggable={true}
        onDragStart={this.dragStart}
        // onDrop={this.drop}
        onDragOver={(event) => event.preventDefault()}
        onDragEnd={this.dragEnd}
        style={style}
      >
      {/* <div className="midbar-shelf-header">source tables</div> */}
      {content}
      </div>
    );
  }
}
