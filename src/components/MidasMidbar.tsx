import React, { MouseEventHandler } from "react";
import {SelectionShelf} from "./SelectionShelf";
import {ColumnShelf} from "./ColumnShelf";

export default class MidasMidbar extends React.Component<{}, {}> {
    render() {
        return (
          <>
            <div><h1 className="midbar-shelf-header">Column Shelf</h1><ColumnShelf ref={comp => window.columnShelf = comp}/></div>
            <div><h1 className="midbar-shelf-header">Selection Shelf</h1><SelectionShelf ref={comp => window.selectionShelf = comp}/>
            </div>
          </>
        );
    }
}