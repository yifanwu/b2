/// <reference path="../external/Jupyter.d.ts" />
import React, { MouseEventHandler } from "react";
import {
  SortableContainer,
  SortableElement,
  SortableHandle,
} from "react-sortable-hoc";
import { makeElementId } from "../config";
import { View } from "vega";
// we are going to be rendering vega-lite now for its superior layout etc.
import { TopLevelSpec } from "vega-lite";
import vegaEmbed from "vega-embed";
import { SELECTION_SIGNAL, DEFAULT_DATA_SOURCE, DEBOUNCE_RATE } from "../constants";
import { LogDebug, LogInternalError, getDfId, getDigitsToRound, navigateToNotebookCell } from "../utils";
import CellManager from "../CellManager";
import { EncodingSpec, genVegaSpec } from "../charts/vegaGen";

interface MidasElementProps {
  changeStep: number;
  cellId: string;
  removeChart: MouseEventHandler;
  dfName: string;
  title: string;
  encoding: EncodingSpec;
  tick: (dfName: string) => void;
  cellState: CellManager;
  data: any[];
  comm: any; // unfortunately not typed
}

interface MidasElementState {
  elementId: string;
  hidden: boolean;
  view: View;
  currentBrush: string;
}

const DragHandle = SortableHandle(() => <span className="drag-handle"><b>&nbsp;⋮⋮&nbsp;</b></span>);
// in theory they should each have their own call back,
// but in practice, there is only one selection happening at a time due to single user



/**
 * Contains the visualization as well as a header with actions to minimize,
 * delete, or find the corresponding cell of the visualization.
 */
export class MidasElement extends React.Component<MidasElementProps, MidasElementState> {
  constructor(props: any) {
    super(props);
    this.embed = this.embed.bind(this);
    this.addBrush = this.addBrush.bind(this);
    this.getDebouncedFunction = this.getDebouncedFunction.bind(this);

    const elementId = makeElementId(this.props.dfName, false);
    this.state = {
      hidden: false,
      view: null,
      elementId,
      currentBrush: null,
    };
  }

  componentDidMount() {
    // FIXME: maybe do not need to run everytime???
    this.embed();
  }

  addBrush(selectionStr: string) {
    if (selectionStr === this.state.currentBrush) {
      LogDebug(`add brush called ${selectionStr}, NOOP`);
      return;
    }
    const selection = JSON.parse(selectionStr);
    // @ts-ignore
    const scale = this.state.view.scale;
    const signal = this.state.view.signal;
    const encoding = this.props.encoding;
    if (selection[encoding.x]) {
      const x_pixel_min = scale("x")(selection[encoding.x][0]);
      const l = selection[encoding.x].length;
      const x_pixel_max = scale("x")(selection[encoding.x][l - 1]);
      // and update the brush_x and brush_y
      signal("brush_x", [x_pixel_min, x_pixel_max]);
    }
    if (selection[encoding.y]) {
      const y_pixel_min = scale("y")(selection[encoding.y][0]);
      const y_pixel_max = scale("y")(selection[encoding.y][1]);
      // and update the brush_y and brush_y
      signal("brush_y", [y_pixel_min, y_pixel_max]);
    }
    return;
  }

  roundIfPossible(selection: any) {
    const encoding = this.props.encoding;
    if (encoding.shape !== "bar") {

      let rounedEncoding: any = {};
      // {"horsepower: []"}
      if (selection[encoding.x]) {
        // if it's number
        // get diff
        const digits = getDigitsToRound(selection[encoding.x][1], selection[encoding.x][0]);
        rounedEncoding[encoding.x] = selection[encoding.x].map((v: number) => Math.round(v * digits) / digits);
      }
      if (selection[encoding.y]) {
        const digits = getDigitsToRound(selection[encoding.y][1], selection[encoding.y][0]);
        rounedEncoding[encoding.y] = selection[encoding.y].map((v: number) => Math.round(v * digits) / digits);
      }
      return rounedEncoding;
    } else {
      return selection;
    }
  }

  getDebouncedFunction(dfName: string) {
    const callback = (signalName: string, value: any) => {
      // also need to call into python state...
      let processedValue = {};
      processedValue[dfName] = this.roundIfPossible(value);
      let valueStr = JSON.stringify(processedValue);
      valueStr = (valueStr === "null") ? "None" : valueStr;
      this.props.comm.send({
        "command": "add_current_selection",
        "value": valueStr
      });
      // this.props.cellState.addSelectionToPython(dfName, valueStr);
      this.setState({currentBrush: valueStr});
      LogDebug("Sending to comm the selection");
      this.props.tick(dfName);
    };

    const wrapped = (name: any, value: any) => {
      const n = new Date();
      let l = (window as any).lastInvoked;
      (window as any).lastInvoked = n;
      if (l) {
        if ((n.getTime() - l.getTime()) < DEBOUNCE_RATE) {
          clearTimeout((window as any).lastInvokedTimer);
        }
        (window as any).lastInvokedTimer = setTimeout(() => callback(name, value), DEBOUNCE_RATE);
      } else {
        l = n;
      }
    };
    return wrapped;
  }

  embed() {
    const { dfName, encoding, data, tick, cellState } = this.props;
    const vegaSpec = genVegaSpec(encoding, dfName, data);
    // @ts-ignore
    vegaEmbed(`#${this.state.elementId}`, vegaSpec)
      .then((res: any) => {
        const view = res.view;
        this.setState({
          view,
        });
        (window as any)[`view_${dfName}`] = view;
        const cb = this.getDebouncedFunction(dfName);
        res.view.addSignalListener(SELECTION_SIGNAL, cb);
      })
      .catch((err: Error) => console.error(err));
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
    navigateToNotebookCell(this.props.cellId);
  }

  // FIXME: figure out the type...
  async replaceData(newValues: any) {
    if (!this.state.view) {
      LogInternalError(`Vega view should have already been defined by now!`);
    }
    // can do this in python too
    const changeSet = this.state.view
      .changeset()
      .remove((datum: any) => {return datum.is_overview === false; })
      .insert(newValues);

    this.state.view.change(DEFAULT_DATA_SOURCE, changeSet).runAsync();
  }

  /**
   * Renders this component.
   */
  render() {
    return (
      <div className="card midas-element" id={getDfId(this.props.dfName)}>
        <div className="midas-header">
          <DragHandle/>
          <span className="midas-title">{this.props.title}</span>
          <div className="midas-header-options"></div>
          <button
            className={"midas-header-button"}
            onClick={() => this.selectCell()}
          >cell</button>
          <button
            className={"midas-header-button"}
            onClick={() => this.toggleHiddenStatus()}>
            {this.state.hidden ? "+" : "-"}
          </button>
          <button
            className={"midas-header-button"}
            onClick={(e) => this.props.removeChart(e)}>
            x
          </button>
        </div>
        <div
          id={this.state.elementId}
          style={this.state.hidden ? { display: "none" } : {}}
        />
      </div>
    );
  }
}

// const SortableItem = SortableElement((props: MidasElementProps) => (
//   <div className="sortable">
//     <MidasElement {...props}/>
//   </div>
// ), {withRef: true});

// export default SortableItem;

export default MidasElement;