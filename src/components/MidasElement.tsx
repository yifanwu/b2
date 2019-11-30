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
import { LogDebug, LogInternalError, get_df_id } from "../utils";

interface MidasElementProps {
  changeStep: number;
  newData?: any[];
  cellId: number;
  removeChart: MouseEventHandler;
  dfName: string;
  title: string;
  vegaSpec: TopLevelSpec;
  tick: (dfName: string) => void;
  comm: any; // unfortunately not typed
}

interface MidasElementState {
  elementId: string;
  hidden: boolean;
  view: View;
  // both are initial domains that we are fixing
  // yDomain: any;
  // xDomain: any;
}

const DragHandle = SortableHandle(() => <span className="drag-handle"><b>&nbsp;⋮⋮&nbsp;</b></span>);
// in theory they should each have their own call back,
// but in practice, there is only one selection happening at a time due to single user

function getDebouncedFunction(dfName: string, tick: (dfName: string) => void) {
  const callback = (signalName: string, value: any) => {
    // also need to call into python state...
    let valueStr = JSON.stringify(value);
    valueStr = (valueStr === "null") ? "None" : valueStr;

    const c = Jupyter.notebook.insert_cell_above("code");
    const date = new Date().toLocaleString("en-US");
    const text = `# [MIDAS] You selected the following from ${dfName} at time ${date}\nm.add_selection_by_interaction("${dfName}", ${valueStr})`;
    c.set_text(text);
    c.execute();
    LogDebug("Sending to comm the selection");
    tick(dfName);
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


/**
 * Contains the visualization as well as a header with actions to minimize,
 * delete, or find the corresponding cell of the visualization.
 */
export class MidasElement extends React.Component<MidasElementProps, MidasElementState> {
  constructor(props: any) {
    super(props);
    this.embed = this.embed.bind(this);
    const elementId = makeElementId(this.props.dfName, false);
    this.state = {
      hidden: false,
      view: null,
      elementId,
      // yDomain: null,
      // xDomain: null
    };
  }

  componentDidMount() {
    // FIXME: maybe do not need to run everytime???
    this.embed();
  }


  embed() {
    const { dfName, vegaSpec, tick } = this.props;
    vegaEmbed(`#${this.state.elementId}`, vegaSpec)
      .then((res: any) => {
        const view = res.view;
        // const xDomain = view.scale(X_SCALE).domain();
        // const yDomain = view.scale(Y_SCALE).domain();
        this.setState({
          view,
          // xDomain,
          // yDomain
        });
        // this.state.view.signal(Y_DOMAIN_SIGNAL, yDomain);
        // this.state.view.signal(X_DOMAIN_SIGNAL, xDomain);
        LogDebug(`Registering signal for TICK, with signal ${SELECTION_SIGNAL}`);
        res.view.addSignalListener(SELECTION_SIGNAL, getDebouncedFunction(dfName, tick));
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


  componentWillReceiveProps(nextProps: MidasElementProps) {
    if (nextProps.changeStep > this.props.changeStep) {
      const newValues = nextProps.newData;
      // can do this in python too
      const changeSet = this.state.view
        .changeset()
        .remove((datum: any) => { datum.is_overview === 0; })
        .insert(newValues);

      this.state.view.change(DEFAULT_DATA_SOURCE, changeSet).runAsync();
    }
  }

  /**
   * Selects the cell in the notebook where the data frame was defined.
   * Note that currently if the output was generated and then the page
   * is refreshed, this may not work.
   */
  selectCell() {
    const cell = Jupyter.notebook.get_msg_cell(this.props.cellId);
    const index = Jupyter.notebook.find_cell_index(cell);
    Jupyter.notebook.select(index);
    const cell_div = Jupyter.CodeCell.msg_cells[this.props.cellId];
    if (cell_div) {
      cell_div.code_mirror.display.lineDiv.scrollIntoViewIfNeeded();
    }
  }

  getPythonButtonClicked() {
    const execute = `m.js_get_current_chart_code('${this.props.dfName}')`;
    console.log("clicked, and executing", execute);
    IPython.notebook.kernel.execute(execute);
  }

  // FIXME: figure out the type...
  async replaceData(newValues: any) {
    if (!this.state.view) {
      LogInternalError(`Vega view should have already been defined by now!`);
    }
    const filter = new Function(
      "datum",
      "return (true))"
    );
    const changeSet = this.state.view
      .changeset()
      .insert(newValues)
      .remove(filter);

    await this.state.view.change(DEFAULT_DATA_SOURCE, changeSet).runAsync();

  }

  addSelectionButtonClicked() {
    // const execute = `m.js_add_selection_to_shelf('${this.props.title}')`;
    // console.log("clicked, and executing", execute);
    // IPython.notebook.kernel.execute(execute);
    // we want to send this to comm
    this.props.comm.send({
      "command": "get_code_clipboard",
      "df_name": this.props.title
    });
  }

  /**
   * Renders this component.
   */
  render() {
    return (
      <div className="midas-element" id={get_df_id(this.props.dfName)}>
        <div className="midas-header">
          <DragHandle/>
          <span className="midas-title">{this.props.title}</span>
          <div className="midas-header-options"></div>
          <button
            className={"midas-header-button"}
            onClick={() => this.getPythonButtonClicked()}>
            code
          </button>
          <button
            className={"midas-header-button"}
            onClick={() => this.selectCell()}
          >cell</button>
          <button
            className={"midas-header-button"}
            onClick={() => this.addSelectionButtonClicked()}
          >clip</button>
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

const SortableItem = SortableElement((props: MidasElementProps) => (
  <div className="sortable">
    <MidasElement {...props}/>
  </div>
));

export default SortableItem;

// export default MidasElement;