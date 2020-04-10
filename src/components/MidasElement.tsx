/// <reference path="../external/Jupyter.d.ts" />
import React, { RefObject } from "react";
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
import { LogDebug, LogInternalError, getDfId, getDigitsToRound, navigateToNotebookCell, isFirstSelectionContainedBySecond, getMultiClickValue, copyTextToClipboard, getChartDetailId, disableMidasInteractions } from "../utils";
import { LogDataframeInteraction, LogSelection } from "../logging";

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
  hasFilteredValues: boolean;
  code: string;
  isBaseShown: boolean;
  generatedCells: any[];
  currentBrush: PerChartSelectionValue;
  // isOpen: boolean;
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
  private myRef: RefObject<HTMLDivElement>;

  constructor(props: any) {
    super(props);
    this.embed = this.embed.bind(this);
    this.hasSelection = this.hasSelection.bind(this);
    this.updateSelectionMarks = this.updateSelectionMarks.bind(this);
    this.getDebouncedFunction = this.getDebouncedFunction.bind(this);
    this.changeVisual = this.changeVisual.bind(this);
    this.toggleHiddenStatus = this.toggleHiddenStatus.bind(this);
    this.snapToCell = this.snapToCell.bind(this);
    this.move = this.move.bind(this);
    this.getCode = this.getCode.bind(this);
    this.toggleBaseData = this.toggleBaseData.bind(this);

    this.myRef = React.createRef<HTMLDivElement>();
    const elementId = makeElementId(this.props.dfName, false);
    this.state = {
      hidden: false,
      view: null,
      code: null,
      elementId,
      generatedCells: [],
      currentBrush: null,
      isBaseShown: true,
      hasFilteredValues: false,
      // isOpen: false,
    };
  }

  componentDidMount() {
    // FIXME: maybe do not need to run everytime???
    this.embed();
    this.myRef.current.scrollIntoView();
    // also add the click to close the elipsis
    const detailsId = getChartDetailId(this.props.dfName);
    const details = document.getElementById(detailsId);
    const documentClickHandler = (ev: MouseEvent) => {
      if (!details.contains(ev.target as any)) {
        details.removeAttribute("open");
      }
    };
    document.addEventListener("click", documentClickHandler);
  }

  isMultiSelect() {
    return this.props.encoding.selectionType === "multiclick";
  }


  async updateSelectionMarks(selection: PerChartSelectionValue) {
    if (isFirstSelectionContainedBySecond(selection, this.state.currentBrush)) {
      return;
    }

    this.setState({ currentBrush: selection });
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
      return;
    }
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
    return;
  }

  roundIfPossible(selection: any) {
    const encoding = this.props.encoding;
    let rounedEncoding: any = Object.assign({}, selection);
    if (selection[encoding.x] && (encoding.xType === "quantitative")) {
      const digits = getDigitsToRound(selection[encoding.x][0], selection[encoding.x][1]);
      rounedEncoding[encoding.x] = selection[encoding.x].map((v: number) => Math.round(v * digits) / digits);
    }
    if (selection[encoding.y] && (encoding.yType === "quantitative")) {
      const digits = getDigitsToRound(selection[encoding.y][0], selection[encoding.y][1]);
      rounedEncoding[encoding.y] = selection[encoding.y].map((v: number) => Math.round(v * digits) / digits);
    }
    return rounedEncoding;
  }

  getDebouncedFunction(dfName: string) {
    const callback = (signalName: string, value: any) => {
      let processedValue = {};
      let cleanValue = {};
      // weird, includes vlMulti
      if (!this.isMultiSelect()) {
        cleanValue = this.roundIfPossible(value);
      } else {
        delete value["vlMulti"];
        cleanValue = value;
      }
      if (this.updatedSelection && isFirstSelectionContainedBySecond(cleanValue, this.updatedSelection)) {
        return;
      }
      this.updatedSelection = null;
      processedValue[dfName] = cleanValue;
      let valueStr = JSON.stringify(processedValue);
      valueStr = (valueStr === "null") ? "None" : valueStr;
      // we have to disable here, and wait for kernel_idle to release it
      disableMidasInteractions();
      const entry: LogSelection = {
        action: "ui_selection",
        actionKind: "selection",
        dfName: this.props.dfName,
        selection: cleanValue
      };
      this.props.functions.logger(entry);
      this.props.functions.addCurrentSelectionMsg(valueStr);
      this.setState({ currentBrush: cleanValue });
      LogDebug(`Chart causing selection ${valueStr}`);
      this.props.functions.setUIItxFocus(this.props.dfName);
      // have to set focus manually because the focus is not set
      document.getElementById(getDfId(this.props.dfName)).focus();
    };
    // Note that debouncing is not just good to lower perf load
    // If there were multiple verga triggered in a sequence programmatically, we'll just do the final thing at the end.
    const wrapped = (name: any, value: any) => {
      const n = new Date();
      let l = (window as any).lastInvoked;
      (window as any).lastInvoked = n;
      if (!l) {
        // initial case
        l = n;
      }
      if ((n.getTime() - l.getTime()) < DEBOUNCE_RATE) {
        clearTimeout((window as any).lastInvokedTimer);
      }
      (window as any).lastInvokedTimer = setTimeout(() => {
        if ((window as any).midasSelectionEnabled) {
          callback(name, value);
        } else {
          LogDebug("Cannot execute when kernel is busy!");
        }
      }, DEBOUNCE_RATE);
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
      const action = prevState.hidden ? "show_chart" : "hide_chart";
      const entry: LogDataframeInteraction = {
        action,
        actionKind: "ui_control",
        dfName:  this.props.dfName,
      };
      this.props.functions.logger(entry);
      return {
        hidden: !prevState.hidden,
        // isOpen: false
      };
    });
  }

  toggleBaseData() {
    this.setState(prevState => {
      const entry: LogDataframeInteraction = {
        action: prevState.isBaseShown ? "hide_midas" : "show_midas",
        actionKind: "ui_control",
        dfName:  this.props.dfName,
      };
      this.props.functions.logger(entry);
      if (prevState.isBaseShown) {
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
    // this.props.functions.getChartCode(this.props.dfName);
    navigateToNotebookCell(this.props.cellId);
    const entry: LogDataframeInteraction = {
      action: "navigate_to_definition_cell",
      actionKind: "interaction2coding",
      dfName: this.props.dfName,
    };
    this.props.functions.logger(entry);
  }

  /**
   * currently called by the snapshot
   */
  getCode() {
    const code = this.state.code
      ? this.state.code
      : this.props.code;
    return code;
  }

  copyCodeToClipboard() {
    // this.props.functions.getCode(this.props.dfName);
    // adding a new line because in the cell new line is annoying
    copyTextToClipboard(this.getCode() + "\n");
    const entry: LogDataframeInteraction = {
      action: "get_code",
      actionKind: "interaction2coding",
      dfName: this.props.dfName,
    };
    this.props.functions.logger(entry);
  }

  getSvg(): Promise<string> {
    return this.state.view.toSVG();
  }

  snapToCell() {
    // get the current svg
    // lame comments for now (maybe: code and selection, for the future)
    const executeCapturedCells = this.props.functions.executeCapturedCells;
    const comments = this.props.dfName;
    const entry: LogDataframeInteraction = {
      action: "snapshot_single",
      actionKind: "interaction2coding",
      dfName: this.props.dfName,
    };
    this.props.functions.logger(entry);

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
    const hasFilteredValues = newValues.length > 0
      ? true
      : false
      ;

    // if there is not filtered values, then we also need to make sure that the isBaseShown is true
    this.setState(prevState => {
      if ((!hasFilteredValues) && (!prevState.isBaseShown)) {
        this.toggleBaseData();
      }
      return {
        code,
        hasFilteredValues,
      };
    });
  }

  move(direction: "left" | "right") {
    this.props.moveElement(direction);
    const entry: LogDataframeInteraction = {
      action: "move_chart",
      actionKind: "ui_control",
      dfName: this.props.dfName,
    };
    this.props.functions.logger(entry);
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
    const toggleSummaryPin = this.state.hasFilteredValues
      ? this.state.isBaseShown
        ? <a onClick={() => this.toggleBaseData()}>{"📌 show filtered data only"}</a>
        : <a onClick={() => this.toggleBaseData()}>{"📍 show original and filtered"}</a>
      : null
      ;

    return (
      <div
        ref={this.myRef}
        className={className}
        id={getDfId(this.props.dfName)}
        tabIndex={-1}
        onBlur={() => {
            this.props.functions.setUIItxFocus();
          }}>
        <div className="midas-header">
          <span>{this.props.title} </span>
          {/*  open={this.state.isOpen} */}
          <details title="click to see options" id={getChartDetailId(this.props.dfName)}>
            <summary>
              {DetailButton}
            </summary>
            <div className="midas-chart-action">
              {toggleSummaryPin}
              <a title="Snap an image of chat to notebook" onClick={() => this.snapToCell()}>📷 snapshot to notebook</a>
              <a title="Copy data query code to clopboard" onClick={() => this.copyCodeToClipboard()}>📋 copy code to clipboard</a>
              <a title="Copy visual code definitions to clippboard" onClick={() => this.changeVisual()}>📊 find defining cell</a>
              <a title="Move chart left" onClick={() => this.move("left")}>⬅️ move left</a>
              <a title="Move chart right" onClick={() => this.move("right")}>➡️ move right</a>
              <a title={this.state.hidden ? "Open the chart" : "Fold the chart"} onClick={() => this.toggleHiddenStatus()}>{this.state.hidden ? "➕ maximize chart" : "➖ minimize chart"} </a>
              <a title="Remove the chart" onClick={() => this.props.removeChart()}>❌ delete chart</a>
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