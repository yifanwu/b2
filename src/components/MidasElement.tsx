/// <reference path="../external/Jupyter.d.ts" />
import React, { MouseEventHandler } from "react";
import {
  SortableContainer,
  SortableElement,
  SortableHandle,
} from 'react-sortable-hoc';

interface MidasElementProps {
  id: number;
  onClick: MouseEventHandler;
  name: string;
  getCellId: Function;
  fixYScale: () => void;
}

interface MidasElementState {
  hidden: boolean;
}

const DragHandle = SortableHandle(() => <span className="drag-handle"><b>&nbsp;⋮⋮&nbsp;</b></span>);

/**
 * Contains the visualization as well as a header with actions to minimize,
 * delete, or find the corresponding cell of the visualization.
 */
class MidasElement extends React.Component<MidasElementProps, MidasElementState> {
    constructor(props: MidasElementProps) {
      super(props);
      this.state = { hidden: false };
    }

    /**
     * Toggles whether the visualization can be seen
     */
    toggleHiddenStatus() {
      this.setState(prevState => {
        return { hidden: !prevState.hidden };
      });
    }
    /**
     * Selects the cell in the notebook where the data frame was defined.
     * Note that currently if the output was generated and then the page
     * is refreshed, this may not work.
     */
    selectCell() {
      let cell = Jupyter.notebook.get_msg_cell(this.props.getCellId());
      let index = Jupyter.notebook.find_cell_index(cell);
      Jupyter.notebook.select(index);
    }

    getPythonButtonClicked() {
      const execute = `m.js_get_current_chart_code('${this.props.name}')`;
      console.log("clicked, and executing", execute);
      IPython.notebook.kernel.execute(execute);
    }

    /**
     * Renders this component.
     */
    render() {
      return (
        <div className="midas-element">
          <div className="midas-header">
            <DragHandle/>
            <span className="midas-title">{this.props.name}</span>
            <div className="midas-header-options"></div>
            <button
              className={"midas-header-button"}
              onClick={() => this.props.fixYScale()}>
              Fix Y
            </button>
            <button
              className={"midas-header-button"}
              onClick={() => this.getPythonButtonClicked()}>
              Code
            </button>
            <button
              className={"midas-header-button"}
              onClick={() => this.selectCell()}
            >Cell</button>
            <button
              className={"midas-header-button"}
              onClick={() => this.toggleHiddenStatus()}>
              {this.state.hidden ? "+" : "-"}
            </button>
            <button
              className={"midas-header-button"}
              onClick={(e) => this.props.onClick(e)}>
              x
            </button>
          </div>
          <div
            id={makeElementId(this.props.id)}
            style={this.state.hidden ? { display: "none" } : {}}
          />
        </div>
      );
    }
    // render() {
    //   return (
    //     <div>
    //       <DragHandle/>
    //       Test
    //     </div>
    //   )
    // }
  }

/**
 * Returns the DOM id of the given element that contains the visualizations
 * @param id the id of the data frame of the visualization
 * @param includeSelector whether to include CSS selector (#)
 */
function makeElementId(id: number, includeSelector: boolean = false) {
  let toReturn = `midas-element-${id}`;
  return includeSelector ? "#" + toReturn : toReturn;
}

const SortableItem = SortableElement((props: MidasElementProps) => (
  <div className="sortable">
    <MidasElement {...props}/>
  </div>
));

export default SortableItem;
