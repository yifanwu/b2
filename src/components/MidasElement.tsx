/// <reference path="../external/Jupyter.d.ts" />
import React, { MouseEventHandler } from "react";
import {
  SortableContainer,
  SortableElement,
  SortableHandle,
} from 'react-sortable-hoc';
import { makeElementId } from "../config";
import { Spec, View } from "vega";
import vegaEmbed from "vega-embed";
import { MIDAS_INSTANCE_NAME, SELECTION_SIGNAL, DEFAULT_DATA_SOURCE, Y_DOMAIN_SIGNAL, DEBOUNCE_RATE } from "../constants";
import { LogDebug, LogInternalError } from "../utils";

interface MidasElementProps {
  cellId: number;
  removeChart: MouseEventHandler;
  dfName: string;
  title: string;
  vegaSpec: Spec;
}

interface MidasElementState {
  elementId: string;
  hidden: boolean;
  view: View;
}

const DragHandle = SortableHandle(() => <span className="drag-handle"><b>&nbsp;⋮⋮&nbsp;</b></span>);
// in theory they should each have their own call back,
// but in practice, there is only one selection happening at a time due to single user

function getDebouncedFunction(dfName: string) {
  const callback = (signalName: string, value: any) => {
    // also need to call into python state...
    const valueStr = JSON.stringify(value);
    const pythonCommand = `${MIDAS_INSTANCE_NAME}.js_add_selection("${dfName}", '${valueStr}')`;
    IPython.notebook.kernel.execute(pythonCommand);
    // FIXME: there might be some async issues between the midas and the python
    window.midas.tick(dfName);
  };

  const wrapped = (name: any, value: any) => {
    const n = new Date();
    let l = (window as any).lastInvoked;
    (window as any).lastInvoked = n;
    // const cb = new Function("name", "value", callback);
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
    };
  }

  componentDidMount() {
    // FIXME: maybe do not need to run everytime???
    this.embed();
  }

  embed() {
    const { dfName, vegaSpec } = this.props;
    // TODO: add options support later...
    // not sure why they have this http loader thing
    // , {
    //   loader: { http: { credentials: "same-origin" } }
    // }
    vegaEmbed(`#${this.state.elementId}`, vegaSpec)
      .then((res: any) => {
        this.setState({view: res.view});
        // also update this view such that it calls the Midas tick everytime it changes...
        LogDebug(`Registering signal for TICK`);
        // this is the first time we are registering the signal, hence set signal
        // for the future, it should be addSignalListener, though they should be handled
        res.view.signal(SELECTION_SIGNAL, getDebouncedFunction(dfName));
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
    let cell = Jupyter.notebook.get_msg_cell(this.props.cellId);
    let index = Jupyter.notebook.find_cell_index(cell);
    Jupyter.notebook.select(index);
    Jupyter.CodeCell.msg_cells[this.props.cellId].code_mirror.display.lineDiv.scrollIntoViewIfNeeded()
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

  /**
   * Renders this component.
   */
  render() {
    const fixYScale = () => {
      console.log("FIXING Y");
        // access the current scale
        // @ts-ignore
        const y_scale = this.view.scale(Y_SCALE);
        // then set the current scale
        this.state.view.signal(Y_DOMAIN_SIGNAL, y_scale.domain());
    };
    return (
      <div className="midas-element">
        <div className="midas-header">
          <DragHandle/>
          <span className="midas-title">{this.props.title}</span>
          <div className="midas-header-options"></div>
          <button
            className={"midas-header-button"}
            onClick={() => fixYScale()}>
            Fix Y scale
          </button>
          <button
            className={"midas-header-button"}
            onClick={() => this.getPythonButtonClicked()}>
            get code
          </button>
          <button
            className={"midas-header-button"}
            onClick={() => this.selectCell()}
          >find original cell</button>
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