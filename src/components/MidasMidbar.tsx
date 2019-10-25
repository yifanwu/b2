import React, { MouseEventHandler } from "react";

export default class MidasMidbar extends React.Component<{}, {}> {
    render() {
        return (
          <div id="midas-midbar">
            <div>
              <h1 className="midbar-shelf-header">
                Column Shelf
                </h1>
                <ColumnShelf/>
              </div>
            <div>
              <h1 className="midbar-shelf-header">
                Selection Shelf
              </h1>
              <SelectionShelf/>
            </div>
          </div>
        );
    }
}