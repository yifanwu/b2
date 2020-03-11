/// <reference path="../external/Jupyter.d.ts" />
import React from "react";
// import {
//   SortableContainer,
//   SortableElement,
//   SortableHandle,
// } from "react-sortable-hoc";
import { View } from "vega";
import vegaEmbed from "vega-embed";

import { EncodingSpec, genVegaSpec, multiSelectedField } from "../charts/vegaGen";
import { makeElementId } from "../config";
import { BRUSH_SIGNAL, DEFAULT_DATA_SOURCE, DEBOUNCE_RATE, MIN_BRUSH_PX, BRUSH_X_SIGNAL, BRUSH_Y_SIGNAL, MULTICLICK_SIGNAL, MULTICLICK_TOGGLE, MULTICLICK_PIXEL_SIGNAL, EmbedConfig } from "../constants";
import { PerChartSelectionValue, MidasElementFunctions } from "../types";
import { LogDebug, LogInternalError, getDfId, getDigitsToRound, navigateToNotebookCell, isFirstSelectionContainedBySecond, getMultiClickValue, copyTextToClipboard } from "../utils";

const DetailButton = <svg viewBox="0 0 16 16" fill="currentColor" stroke="none" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" width="14" height="14">
  <circle r="2" cy="8" cx="2"></circle>
  <circle r="2" cy="8" cx="8"></circle>
  <circle r="2" cy="8" cx="14"></circle>
</svg>;

interface MidasElementProps {
  changeStep: number;
  cellId: string;
  removeChart: () => void;
  dfName: string;
  title: string;
  code: string;
  encoding: EncodingSpec;
  data: any[];
  moveElement: (direction: "left" | "right") => void;
  functions: MidasElementFunctions;
}

interface MidasElementState {
  elementId: string;
  hidden: boolean;
  view: View;
  code: string;
  isBaseShown: boolean;
  generatedCells: any[];
  currentBrush: PerChartSelectionValue;
}

// const DragHandle = SortableHandle(() => <span className="drag-handle"><b>&nbsp;⋮⋮&nbsp;</b></span>);
// in theory they should each have their own call back,
// but in practice, there is only one selection happening at a time due to single user

/**
 * Contains the visualization as well as a header with actions to minimize,
 * delete, or find the corresponding cell of the visualization.
 */
export class MidasElement extends React.Component<MidasElementProps, MidasElementState> {
  // activateSignalFlag: boolean;
  updatedSelection: PerChartSelectionValue;

  constructor(props: any) {
    super(props);
    this.embed = this.embed.bind(this);
    this.hasSelection = this.hasSelection.bind(this);
    this.updateSelectionMarks = this.updateSelectionMarks.bind(this);
    this.getDebouncedFunction = this.getDebouncedFunction.bind(this);
    this.changeVisual = this.changeVisual.bind(this);
    this.toggleHiddenStatus = this.toggleHiddenStatus.bind(this);
    this.snapToCell = this.snapToCell.bind(this);
    this.moveLeft = this.moveLeft.bind(this);
    this.moveRight = this.moveRight.bind(this);
    this.getCode = this.getCode.bind(this);
    this.toggleBaseData = this.toggleBaseData.bind(this);
    // this.shouldActivateSignal = this.shouldActivateSignal.bind(this);

    // this.activateSignalFlag = true; // hack
    const elementId = makeElementId(this.props.dfName, false);
    this.state = {
      hidden: false,
      view: null,
      code: null,
      elementId,
      generatedCells: [],
      currentBrush: null,
      isBaseShown: true,
    };
  }

  componentDidMount() {
    // FIXME: maybe do not need to run everytime???
    this.embed();
  }

  isMultiSelect() {
    return this.props.encoding.selectionType === "multiclick";
  }

  // shouldActivateSignal() {
  //   return this.activateSignalFlag;
  // }

  async updateSelectionMarks(selection: PerChartSelectionValue) {
    if (isFirstSelectionContainedBySecond(selection, this.state.currentBrush) ) {
      // LogDebug("BRUSH NOOP", [selection, this.state.currentBrush]);
      return;
    }

    this.setState({ currentBrush: selection });
    // this.activateSignalFlag = false;
    this.updatedSelection = selection;
    const signal = this.state.view.signal.bind(this.state.view);
    const runAsync = this.state.view.runAsync.bind(this.state.view);
    if (Object.keys(selection).length === 0) {
      if (this.isMultiSelect()) {
        signal(MULTICLICK_TOGGLE, false);
        signal(MULTICLICK_PIXEL_SIGNAL, null);
      } else {
        signal(BRUSH_X_SIGNAL, [0, 0]);
      }
      await runAsync();
      // this.activateSignalFlag = true;
      return;
    }
    // LogDebug(`BRUSHING`, [selection, this.state.currentBrush]);
    // @ts-ignore because the vega view API is not fully TS typed.
    const scale = this.state.view.scale.bind(this.state.view);
    const encoding = this.props.encoding;
    let hasModified = false;
    if (this.isMultiSelect()) {
      const selectedField = multiSelectedField(encoding);
      const values = selection[selectedField];
      signal(MULTICLICK_TOGGLE, false);
      signal(MULTICLICK_PIXEL_SIGNAL, null);
      // if we don't run async here it doesn't actually clear
      // remove the signal for now
      await runAsync();
      signal(MULTICLICK_TOGGLE, true);

      for (let v of values) {
        const signalValue = getMultiClickValue(selectedField, v, encoding.selectionDimensions);
        signal(MULTICLICK_PIXEL_SIGNAL, signalValue);
        await runAsync();
        hasModified = true;
      }
    } else {
      if (selection[encoding.x]) {
        const x_pixel_min = scale("x")(selection[encoding.x][0]);
        const l = selection[encoding.x].length;
        const x_pixel_max = (l > 1)
          ? scale("x")(selection[encoding.x][l - 1])
          : x_pixel_min + MIN_BRUSH_PX;
        LogDebug(`updated brush x: ${x_pixel_min}, ${x_pixel_max}`);
        signal(BRUSH_X_SIGNAL, [x_pixel_min, x_pixel_max]);
        await runAsync();
        hasModified = true;
      }
      if (selection[encoding.y]) {
        const y_pixel_min = scale("y")(selection[encoding.y][0]);
        const y_pixel_max = scale("y")(selection[encoding.y][1]);
        signal(BRUSH_Y_SIGNAL, [y_pixel_min, y_pixel_max]);
        hasModified = true;
        await runAsync();
      }
    }
    if (!hasModified) {
      LogInternalError(`Draw brush didn't modify any scales for selection ${selection}`);
    }
    // this.activateSignalFlag = true;
    // LogDebug("setting flag to true");
    return;
  }

  roundIfPossible(selection: any) {
    const encoding = this.props.encoding;
    let rounedEncoding: any = {};
    if (selection[encoding.x]) {
      const digits = getDigitsToRound(selection[encoding.x][1], selection[encoding.x][0]);
      rounedEncoding[encoding.x] = selection[encoding.x].map((v: number) => Math.round(v * digits) / digits);
    }
    if (selection[encoding.y]) {
      const digits = getDigitsToRound(selection[encoding.y][1], selection[encoding.y][0]);
      rounedEncoding[encoding.y] = selection[encoding.y].map((v: number) => Math.round(v * digits) / digits);
    }
    return rounedEncoding;
  }

  getDebouncedFunction(dfName: string) {
    const callback = (signalName: string, value: any) => {
      // also need to call into python state...
      // LogDebug("activateSignalFlag", this.activateSignalFlag);
      // if (!this.shouldActivateSignal()) {
      //   LogDebug("activateSignalFlag set to false, no-op");
      //   return;
      // }
      let processedValue = {};
      let cleanValue = {};
      // const selectedField = multiSelectedField(this.props.encoding);
      if (!this.isMultiSelect()) {
        cleanValue = this.roundIfPossible(value);
      } else {
        cleanValue = value;
      }
      if (isFirstSelectionContainedBySecond(cleanValue, this.updatedSelection)) {
        return;
      }
      this.updatedSelection = null;
      processedValue[dfName] = cleanValue;
      let valueStr = JSON.stringify(processedValue);
      valueStr = (valueStr === "null") ? "None" : valueStr;
      this.props.functions.addCurrentSelectionMsg(valueStr);
      this.setState({ currentBrush: cleanValue });
      LogDebug(`Chart causing selection ${valueStr}`);
      this.props.functions.setUIItxFocus(this.props.dfName);
      // have to set focus manually because the focus is not set
      document.getElementById(getDfId(this.props.dfName)).focus();
    };
    // huh, debouncing actually helps us! If there were mtulple triggered, we'll just do the new things
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
    vegaEmbed(`#${this.state.elementId}`, vegaSpec, EmbedConfig)
      .then((res: any) => {
        const view = res.view;
        this.setState({
          view,
        });
        (window as any)[`view_${dfName}`] = view;
        if (this.isMultiSelect()) {
          const cb = this.getDebouncedFunction(dfName);
          res.view.addSignalListener(MULTICLICK_SIGNAL, cb);
        } else {
          const cb = this.getDebouncedFunction(dfName);
          res.view.addSignalListener(BRUSH_SIGNAL, cb);
        }
      })
      .catch((err: Error) => console.error(err));
  }

  toggleHiddenStatus() {
    this.setState(prevState => {
      this.props.functions.logEntry("toggle_chart_visibility", this.props.dfName);
      return { hidden: !prevState.hidden };
    });
  }

  toggleBaseData() {
    this.setState(prevState => {
      if (prevState.isBaseShown) {
        // remove it
        const changeSet = this.state.view
          .changeset()
          .remove((datum: any) => { return datum.is_overview === true; });
        this.state.view.change(DEFAULT_DATA_SOURCE, changeSet).runAsync();
        return {isBaseShown: false};
      } else {
        const changeSet = this.state.view
          .changeset()
          .insert(this.props.data);
        this.state.view.change(DEFAULT_DATA_SOURCE, changeSet).runAsync();
        return {isBaseShown: true};
      }
    });
  }

  /**
   * Selects the cell in the notebook where the data frame was defined.
   * Note that currently if the output was generated and then the page
   * is refreshed, this may not work.
   */
  changeVisual() {
    this.props.functions.getChartCode(this.props.dfName);
    navigateToNotebookCell(this.props.cellId);
    this.props.functions.logEntry("change_visual", this.props.dfName);
  }

  /**
   * currently called by the snapshot
   */
  getCode() {
    const code = this.state.code
      ? this.state.code
      : this.props.code;
    // this.props.functions.logEntry("get_code", code);
    return code;
  }

  copyCodeToClipboard() {
    // this.props.functions.getCode(this.props.dfName);
    // adding a new line because in the cell new line is annoying
    copyTextToClipboard(this.getCode() + "\n");
    this.props.functions.logEntry("get_code", this.props.dfName);
  }

  getSvg(): Promise<string> {
    return this.state.view.toSVG();
  }

  snapToCell() {
    // get the current svg
    // lame comments for now (maybe: code and selection, for the future)
    const executeCapturedCells = this.props.functions.executeCapturedCells;
    const comments = this.props.dfName;
    this.props.functions.logEntry("snapshot_single", this.props.dfName);

    this.state.view.toSVG()
      .then(function(svg) {
        executeCapturedCells(`<div>${svg}</div>`, comments);
      })
      .catch(function(err) { console.error(err); });
  }

  // FIXME: define type
  async replaceData(newValues: any, code: string) {
    if (!this.state.view) {
      LogInternalError(`Vega view should have already been defined by now!`);
    }
    const changeSet = this.state.view
      .changeset()
      .remove((datum: any) => { return datum.is_overview === false; })
      .insert(newValues);

    this.state.view.change(DEFAULT_DATA_SOURCE, changeSet).runAsync();
    this.setState({
      code
    });
  }

  moveLeft() {
    this.props.moveElement("left");
    this.props.functions.logEntry("move_chart", this.props.dfName);
  }

  moveRight() {
    this.props.moveElement("right");
    this.props.functions.logEntry("move_chart", this.props.dfName);
  }

  hasSelection() {
    return (this.state.currentBrush) && (Object.keys(this.state.currentBrush).length > 0);
  }

  render() {
    // note that the handlers are in the form  () => fun(), because of scoping issues in javascript
    let className = "card midas-element";
    if (this.hasSelection()) {
      className += " selected-card";
    }
    const toggleSummaryPin = this.state.isBaseShown
      ? " 📌"
      : " 📍";

    return (
      <div className={className} id={getDfId(this.props.dfName)}
        tabIndex={-1}
        onBlur={() => {
            this.props.functions.setUIItxFocus();
          }}>
        <div className="midas-header">
          <span>{this.props.title}</span>
          <a onClick={() => this.toggleBaseData()}>{toggleSummaryPin}</a>
          <details title="click to see options">
            <summary>
              {DetailButton}
            </summary>
            <div className="midas-chart-action">
              <a title="Move chart left" onClick={this.moveLeft}>⬅️</a>
              <a title="Move chart right" onClick={this.moveRight}>➡️</a>
              <a title="Snap an image of chat to notebook" onClick={() => this.snapToCell()}>📷</a>
              <a title="Copy visual code definitions to clippboard" onClick={() => this.changeVisual()}>📊</a>
              <a title="Copy data query code to clopboard" onClick={() => this.copyCodeToClipboard()}>📋</a>
              <a title={this.state.hidden ? "Open the chart" : "Fold the chart"} onClick={() => this.toggleHiddenStatus()}>{this.state.hidden ? "➕" : "➖"}</a>
              <a title="Remove the chart" onClick={() => this.props.removeChart()}>❌</a>
            </div>
          </details>
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