import React, { RefObject } from "react";
import arrayMove from "array-move";
import { TopLevelSpec } from "vega-lite";
import { SortableContainer } from "react-sortable-hoc";

import MidasElement from "./MidasElement";
import { ChartsViewLandingPage } from "./ChartsViewLangingPage";
import { LogInternalError, LogSteps, get_df_id } from "../utils";
import { AlertType } from "../types";
import { ALERT_ALIVE_TIME } from "../constants";

// Mappings
//  this stores the information connecting the cells to
//  we want thtis to be both directions.
interface MappingMetaData {
  dfName: string;
}

// TODO: we need to re
interface ContainerElementState {
  dfName: string;
  notebookCellId: number;
  vegaSpec: TopLevelSpec;
  newData?: any[];
  changeStep: number;
}

interface AlertItem {
  msg: string;
  alertType: AlertType;
  aId: number;
}

interface ContainerState {
  notebookMetaData: MappingMetaData[];
  // TODO: refact the name `elements` --- we now have different visual elements
  elements: ContainerElementState[];
  refs: Map<string, RefObject<HTMLDivElement>>;
  // FIXME: the idToCell might not be needed given that we have refs.
  idToCell: Map<string, number>;
  // maps signals to cellIds
  reactiveCells: Map<string, number[]>;
  allReactiveCells: Set<number>;
  alerts: AlertItem[];
  midasPythonInstanceName: string;
  alertCounter: number;
}

interface ContainerProps {
  comm: any;
}

const MidasSortableContainer = SortableContainer(({children}: {children: any}) => {
  return <div>{children}</div>;
});

/**
 * Container for the MidasElements that hold the visualization.
 */
export default class MidasContainer extends React.Component<ContainerProps, ContainerState> {
  constructor(props?: ContainerProps) {
    super(props);
    this.tick = this.tick.bind(this);
    this.captureCell = this.captureCell.bind(this);
    this.addAlert = this.addAlert.bind(this);

    this.state = {
      alertCounter: 0,
      notebookMetaData: [],
      elements: [],
      refs: new Map(),
      idToCell: new Map(),
      reactiveCells: new Map(),
      allReactiveCells: new Set(),
      alerts: [],
      midasPythonInstanceName: null,
    };
  }


  /**
   * Looks up the id of the notebook cell from which the given data frame was
   * defined.
   * @param name the name of the data frame
   */
  getCellId(name: string) {
    return this.state.idToCell[name];
  }


  setMidasPythonInstanceName(midasPythonInstanceName: string) {
    this.setState({ midasPythonInstanceName });
  }


  /**
   * Stores the cell id at which the given data frame was defined.
   * @param name the name of the data frame
   * @param cell the cell id at which the data frame was defined
   */
  recordDFCellId(name: string, cell: string) {
    this.setState((prevState) => {
      prevState.idToCell[name] = cell;
      return {
        elements: prevState.elements,
        idToCell: prevState.idToCell,
      };
    });
  }


  tick(dfName: string) {
    console.log("midas container tick called", dfName);
    // look up the reactiveCells
    const cells = this.state.reactiveCells.get(dfName);
    if (cells) {
      const cellIdxs = cells.map(c => {
        const cIdxMsg = Jupyter.notebook.get_msg_cell(c);
        const idx = Jupyter.notebook.find_cell_index(cIdxMsg);
        if (idx) {
          return idx;
        } else {
          // maybe report this to the user
          LogInternalError(`One of the cells is no longer found`);
        }
      });
      LogSteps(`[${dfName}] Reactively executing cells ${cellIdxs}`);
      Jupyter.notebook.execute_cells(cellIdxs);
    }
  }


  captureCell(dfName: string, cellId: number) {
    if (this.state.allReactiveCells.has(cellId)) {
      // we have already done this before
      return;
    }
    this.setState(prevState => {
      if (prevState.reactiveCells.has(dfName)) {
        prevState.reactiveCells.get(dfName).push(cellId);
      } else {
        prevState.reactiveCells.set(dfName, [cellId]);
      }
    });
  }


  navigate(dfName: string) {
    // TODO @yifan/@ryan
    const elmnt = document.getElementById(get_df_id(dfName));
    elmnt.scrollIntoView();
  }


  addAlert(msg: string, alertType: AlertType = AlertType.Error) {
    // make this disappearing
    const aId = this.state.alerts.length;
    this.setState(prevState => {
      prevState.alerts.push({
        msg,
        alertType,
        aId
      });
      return prevState;
    });
    const self = this;
    window.setTimeout(() => {
      console.log(`closing alert ${aId}`);
      // just move the alert counter ahead
      self.setState(p => {
        return { alertCounter: p.alertCounter + 1};
      });
    }, ALERT_ALIVE_TIME);
  }


  resetState() {
    // TODO
    throw Error("not implemented");
  }


  /**
   * Adds the visualization of the given data frame to this container
   * @param id the id of the data frame
   * @param dfName the name of the data frame
   */
  addDataFrame(dfName: string, vegaSpec: TopLevelSpec, notebookCellId: number) {
    console.log(`Adding data frame: ${dfName} associated with cell ${notebookCellId}`);
    if (this.state.elements.filter(e => e.dfName === dfName).length > 0) {
      // replace the vega definition, must maintain the element's original position
      this.setState(prevState => {
        const e = prevState.elements.filter(e => e.dfName === dfName)[0];
        e.notebookCellId = notebookCellId;
        e.vegaSpec = vegaSpec;
        e.changeStep = 1;
        return prevState;
      });
      return;
    }

    this.setState(prevState => {
      // see if we need to delete the old one first
      const idx = prevState.elements.findIndex((v) => v.dfName === dfName);
      if (idx > 0) {
        prevState.elements[idx] = {
          notebookCellId,
          dfName,
          vegaSpec,
          changeStep: 1
        };
      } else {
        prevState.elements.push({
          notebookCellId,
          dfName,
          vegaSpec,
          changeStep: 1
        });
      }
      return prevState;
    });
  }


  replaceData(dfName: string, data: any[]) {
    // need to invoke the replaceData function of the child...
    // replaceData
    // this.refLookup[dfName].replaceData();
    this.setState(prevState => {
      for (let e of prevState.elements) {
        if (e.dfName === dfName) {
          e.newData = data;
          e.changeStep = e.changeStep + 1;
        }
      }
      return {
        elements: prevState.elements
      };
    });
  }


  /**
   * Removes the given data frame via id
   * @param key the id of the data frame
   */
  removeDataFrame(dfName: string) {
    this.setState(prevState => {
      return {
        elements: prevState.elements.filter(e => (e.dfName !== dfName))
      };
    });
  }

   onSortEnd = ({oldIndex, newIndex}: {oldIndex: number, newIndex: number}) => {
    this.setState(prevState => {
      return {
        notebookMetaData: prevState.notebookMetaData,
        elements: arrayMove(prevState.elements, oldIndex, newIndex),
        refs: prevState.refs,
        idToCell: prevState.idToCell,
        reactiveCells: prevState.reactiveCells,
        allReactiveCells: prevState.allReactiveCells,
        alerts: prevState.alerts
      };
    });
  }


  render() {
    const { elements, alerts, alertCounter } = this.state;
    const chartDivs = elements.map(({
      notebookCellId, dfName, vegaSpec, changeStep: chanageStep, newData }, index) => {
      return <MidasElement
        index={index}
        cellId={notebookCellId}
        key={dfName}
        dfName={dfName}
        comm={this.props.comm}
        tick={this.tick}
        title={dfName}
        vegaSpec={vegaSpec}
        changeStep={chanageStep}
        newData={newData}
        removeChart={() => this.removeDataFrame(dfName)}
      />;
    });
    const alertDivs = [];
    for (let i = alertCounter; i < alerts.length; i ++) {
      const a = alerts[i];
      const className = a.alertType === AlertType.Error ? "midas-alerts-error" : "midas-alerts-debug";
      alertDivs.push(<div
          className={`card midas-alert ${className}`}
          key={`alert-${a.aId}`}
        >
          {a.msg}
          <button className="notification-btn" onClick={close}>x</button>
      </div>);
    }
    const content = (chartDivs.length > 0) ? <MidasSortableContainer axis="xy" onSortEnd={this.onSortEnd} useDragHandle>{chartDivs}</MidasSortableContainer> : <ChartsViewLandingPage/>;
    return (
      <div id="midas-floater-container">
        {content}
        {alertDivs}
      </div>
    );
  }
}
