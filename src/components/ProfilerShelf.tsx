import React from "react";
import { ColumnItem } from "./ColumnItem";
import { ProfileShelfLandingPage } from "./ProfileShelfLandingPage";

interface ProfilerColumn {
  columnName: string;
  columnType: string;
}

interface ColumnShelfState {
  tables: { [index: string]: ProfilerColumn[] };
}

interface ProfilerShelfProps {
  comm: any;
}

export class ProfilerShelf extends React.Component<ProfilerShelfProps, ColumnShelfState> {
  constructor(props: ProfilerShelfProps) {
    super(props);
    this.columnClicked  = this.columnClicked.bind(this);

    this.state = {
      tables: {},
    };
  }

  addOrReplaceTableItem(tableName: string, columnItems: ProfilerColumn[], cellId: number) {
    // just do nothing with the cellId for now
    this.setState(prevState => {
      prevState.tables[tableName] = columnItems;
      return prevState;
    });
  }

  columnClicked(columnName: string, tableName: string) {
    const payload = {
      command: "column-selected",
      column: columnName,
      df_name: tableName,
    };
    console.log(`Clicked, and sending message with contents ${JSON.stringify(payload)}`);
    this.props.comm.send(payload);
  }

  hideItem(tableName: string, index: number) {
    this.setState(prevState => {
      prevState.tables[tableName].splice(index, 1);
      return prevState;
    });
  }

  render() {
    const tableDivs = Object.keys(this.state.tables).map((tableName) => {
      const columns = this.state.tables[tableName].map((c, i) => <ColumnItem
        key={`column-${tableName}-${c.columnName}`}
        tableName={tableName}
        columnName={c.columnName}
        columnType={c.columnType}
        onClick={() => this.columnClicked(c.columnName, tableName)}
        onDelete={() => this.hideItem(tableName, i)}
      />);
      return <div className="profiler-table" key={`table-${tableName}`}>
        <div className="profiler-table-name">{tableName}</div>
        {columns}
      </div>;
    });
    const content = (tableDivs.length > 0) ? tableDivs : <ProfileShelfLandingPage/>;
    return (
      <div className="shelf" id="profiler-shelf">
      {/* <div className="midbar-shelf-header">source tables</div> */}
      {content}
      </div>
    );
  }
}
