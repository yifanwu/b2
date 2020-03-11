import React from "react";

import { ColumnItem } from "./ColumnItem";
import { ProfileShelfLandingPage } from "./ProfileShelfLandingPage";
import { LogDebug } from "../utils";
import { TOGGLE_PANNEL_BUTTON, PROFILTER_SHELF_WIDTH, CONTAINER_INIT_WIDTHS } from "../constants";

interface ProfilerColumn {
  columnName: string;
  columnType: string;
}

interface ProfilerShelfState {
  tables: { [index: string]: ProfilerColumn[] };
  isShown: { [index: string]: boolean; };
  isShownAll: boolean;
  // dragged: boolean;
  // oldX: number;
  // oldY: number;
  // x: number;
  // y: number;
}

interface ProfilerShelfProps {
  columnSelectMsg: (columnName: string, tableName: string) => void;
  logEntry: (action: string, metadata: string) => void;
}


function createTogglePannelButton(togglePannel: () => void) {
  if (!$(`#${TOGGLE_PANNEL_BUTTON}`).length) {
    // create if does not exist
    const newButton = `<div class="btn-group">
      <button
        id="${TOGGLE_PANNEL_BUTTON}"
        class="btn btn-default one-time-animation"
        title="Toggle the column pannel in the middle"
      >Toggle Column Shelf</button>
    </div>`;
    $("#maintoolbar-container").append(newButton);
  }
  $(`#${TOGGLE_PANNEL_BUTTON}`).click(() => togglePannel());
  return;
}

export class ProfilerShelf extends React.Component<ProfilerShelfProps, ProfilerShelfState> {
  constructor(props: ProfilerShelfProps) {
    super(props);
    this.columnClicked  = this.columnClicked.bind(this);
    this.toggleTable = this.toggleTable.bind(this);
    this.togglePannel = this.togglePannel.bind(this);
    // this.drop = this.drop.bind(this);
    // this.dragEnd = this.dragEnd.bind(this);
    // this.dragStart = this.dragStart.bind(this);
    createTogglePannelButton(this.togglePannel);
    this.state = {
      tables: {},
      isShown: {},
      isShownAll: true,
      // dragged: false,
      // oldX: 0,
      // oldY: 0,
      // x: CONTAINER_INIT_WIDTHS - PROFILTER_SHELF_WIDTH,
      // y: 0,
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

  togglePannel() {
    this.setState(prevState => {
      return { isShownAll: !prevState.isShownAll};
    });
    // also send note
    this.props.logEntry("toggle_shelf", "");
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
        />)
        : [];
      return <div className="profiler-table" key={`table-${tableName}`}>
        <div className="profiler-table-name" onClick={this.toggleTable(tableName)}>{tableName}</div>
        {columns}
      </div>;
    });
    const content = (tableDivs.length > 0)
      ? tableDivs
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
