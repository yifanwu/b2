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
import vegaEmbed from "vega-embed";
import { SELECTION_SIGNAL, DEFAULT_DATA_SOURCE, DEBOUNCE_RATE, MIN_BRUSH_PX, BRUSH_X_SIGNAL, BRUSH_Y_SIGNAL } from "../constants";
import { LogDebug, LogInternalError, getDfId, getDigitsToRound, navigateToNotebookCell, comparePerChartSelection } from "../utils";
import { EncodingSpec, genVegaSpec } from "../charts/vegaGen";
import { PerChartSelectionValue } from "../types";

interface MidasElementProps {
  changeStep: number;
  cellId: string;
  removeChart: MouseEventHandler;
  dfName: string;
  title: string;
  encoding: EncodingSpec;
  tick: (dfName: string) => void;
  data: any[];
  addCurrentSelectionMsg: (value: string) => void;
  getCode: (value: string) => void;
}

interface MidasElementState {
  elementId: string;
  hidden: boolean;
  view: View;
  // both are initial domains that we are fixing
  generatedCells: any[];
  // yDomain: any;
  // xDomain: any;
  currentBrush: PerChartSelectionValue;
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
    this.drawBrush = this.drawBrush.bind(this);
    this.getDebouncedFunction = this.getDebouncedFunction.bind(this);

    const elementId = makeElementId(this.props.dfName, false);
    this.state = {
      hidden: false,
      view: null,
      elementId,
      generatedCells: [],
      // yDomain: null,
      // xDomain: null
      currentBrush: null,
    };
  }

  componentDidMount() {
    // FIXME: maybe do not need to run everytime???
    this.embed();
  }

  // TODO: instead of just supporting brush, also add clicking
  drawBrush(selection: PerChartSelectionValue) { // will be a dictionary...
    if (comparePerChartSelection(selection, this.state.currentBrush) ) {
      LogDebug("BRUSH NOOP", selection);
      return;
    }
    const signal = this.state.view.signal.bind(this.state.view);
    if (Object.keys(selection).length === 0) {
      // make brush null
      signal(SELECTION_SIGNAL, {});
    }
    LogDebug(`BRUSHING`, [selection, this.state.currentBrush]);
    // const selection = JSON.parse(selectionStr);
    // @ts-ignore because the vega view API is not fully TS typed.
    const scale = this.state.view.scale.bind(this.state.view);
    const runAsync = this.state.view.runAsync.bind(this.state.view);
    const encoding = this.props.encoding;
    let hasModified = false;
    if (selection[encoding.x]) {
      const x_pixel_min = scale("x")(selection[encoding.x][0]);
      const l = selection[encoding.x].length;
      const x_pixel_max = (l > 1)
        ? scale("x")(selection[encoding.x][l - 1])
        : x_pixel_min + MIN_BRUSH_PX;
      // and update the brush_x and brush_y
      LogDebug(`updated brush x: ${x_pixel_min}, ${x_pixel_max}`);
      signal(BRUSH_X_SIGNAL, [x_pixel_min, x_pixel_max]);
      runAsync();
      hasModified = true;
    }
    if (selection[encoding.y]) {
      const y_pixel_min = scale("y")(selection[encoding.y][0]);
      const y_pixel_max = scale("y")(selection[encoding.y][1]);
      // and update the brush_y and brush_y
      signal(BRUSH_Y_SIGNAL, [y_pixel_min, y_pixel_max]);
      runAsync();
      hasModified = true;
    }
    if (!hasModified) {
      LogInternalError(`Draw brush didn't modify any scales for selection ${selection}`);
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
      const cleanValue = this.roundIfPossible(value);
      processedValue[dfName] = cleanValue;
      let valueStr = JSON.stringify(processedValue);
      valueStr = (valueStr === "null") ? "None" : valueStr;
      this.props.addCurrentSelectionMsg(valueStr);
      this.setState({ currentBrush: cleanValue });
      LogDebug(`Chart causing selection ${valueStr}`);
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
    const { dfName, encoding, data } = this.props;
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

  getCode() {
    this.props.getCode(this.props.dfName);
  }

  // FIXME: figure out the type...
  async replaceData(newValues: any) {
    if (!this.state.view) {
      LogInternalError(`Vega view should have already been defined by now!`);
    }
    // can do this in python too
    const changeSet = this.state.view
      .changeset()
      .remove((datum: any) => { return datum.is_overview === false; })
      .insert(newValues);

    this.state.view.change(DEFAULT_DATA_SOURCE, changeSet).runAsync();
  }

  clearGeneratedCells() {
    console.log(`There are ${this.state.generatedCells.length} to clear`);
    this.state.generatedCells.forEach(c => {
      console.log(`Deleting cell that exists at index ${Jupyter.notebook.find_cell_index(c)}`);
      Jupyter.notebook.delete_cell(Jupyter.notebook.find_cell_index(c))
    });
    this.setState(prevState => {
      let newState = {
        elementId: prevState.elementId,
        hidden: prevState.hidden,
        view: prevState.view,
        generatedCells: Array<any>(),
      }
      return newState;
    });
  }

  /**
   * Renders this component.
   */
  render() {
    return (
      <div className="card midas-element" id={getDfId(this.props.dfName)}>
        <div className="midas-header">
          <DragHandle />
          <span className="midas-title">{this.props.title}</span>
          <div className="midas-header-options"></div>
          <button
            className={"midas-header-button"}
            onClick={() => this.selectCell()}
          >cell</button>
          <button
            className={"midas-header-button"}
            onClick={() => this.getCode()}
          >code</button>
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