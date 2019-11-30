import React from "react";
import { ColumnItem } from "./ColumnItem";

interface ProfilerColumn {
  columnName: string;
  columnType: string;
}

interface ColumnShelfState {
  tables: { [index: string]: ProfilerColumn[] };
}

export class ProfilerShelf extends React.Component<{}, ColumnShelfState> {
  constructor(props?: {}) {
    super(props);
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
        onDelete={() => this.hideItem(tableName, i)}
      />);
      return <div key={`table-${tableName}`}>
        <div className="profiler-table-name">{tableName}</div>
        {columns}
      </div>;
    });
    return (
      <div id="profiler-shelf">
      <div className="midbar-shelf-header">source tables</div>
        {tableDivs}
      </div>
    );
  }
}
