import React, { createRef, RefObject } from "react";

import MidasElement from "./MidasElement";
import Profiler from "./Profiler";
import { hashCode, LogInternalError, LogSteps } from "../utils";
import { AlertType } from "../types";
import {
  SortableContainer,
  SortableElement,
  SortableHandle,
} from 'react-sortable-hoc';
import { DataProps } from "@nteract/data-explorer/src/types";
import { Spec } from "vega";

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
  vegaSpec: Spec;
}

interface ProfilerInfo {
  dfName: string;
  notebookCellId: number;
  data: DataProps;
}
import arrayMove from 'array-move';

interface AlertItem {
  msg: string;
  alertType: AlertType;
  aId: number;
}

interface ContainerState {
  notebookMetaData: MappingMetaData[];
  profiles: ProfilerInfo[];
  // TODO: refact the name `elements` --- we now have different visual elements it seems.
  elements: ContainerElementState[];
  refs: Map<string, RefObject<HTMLDivElement>>;
  // FIXME: the idToCell might not be needed given that we have refs.
  idToCell: Map<string, number>;
  // maps signals to cellIds
  reactiveCells: Map<string, number[]>;
  allReactiveCells: Set<number>;
  alerts: AlertItem[];
}

const ALERT_ALIVE_TIME = 5000;

const MidasSortableContainer = SortableContainer(({children}: {children: any}) => {
  return <div>{children}</div>;
});

/**
 * Container for the MidasElements that hold the visualization.
 */
export default class MidasContainer extends React.Component<{}, ContainerState> {
  constructor(props?: {}) {
    super(props);

    // NOTE: maybe other binds needed as well...
    this.tick = this.tick.bind(this);
    this.captureCell = this.captureCell.bind(this);
    this.addAlert = this.addAlert.bind(this);

    this.state = {
      notebookMetaData: [],
      profiles: [],
      elements: [],
      refs: new Map(),
      idToCell: new Map(),
      reactiveCells: new Map(),
      allReactiveCells: new Set(),
      alerts: []
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
    // 
    const elmnt = document.getElementById("content");
    elmnt.scrollIntoView();
  }


  addAlert(msg: string, alertType: AlertType = AlertType.Error) {
    // make this disappearing
    const aId = hashCode(msg) * 100 + Math.round(Math.random() * 100);
    this.setState(prevState => {
      prevState.alerts.push({
        msg,
        alertType,
        aId
      });
      return prevState;
    });
    window.setTimeout(() => {
      this.setState(prevState => {
        const alerts = prevState.alerts.filter(a => a.aId !== aId);
        return {
          alerts
        };
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
  addDataFrame(dfName: string, vegaSpec: Spec, notebookCellId: number) {
    console.log(`Adding data frame: ${dfName} associated with cell ${notebookCellId}`)
    if (this.state.elements.filter(e => e.dfName === dfName).length > 0) {
      return;
    }

    this.setState(prevState => {
      prevState.elements.push({
        notebookCellId,
        dfName,
        vegaSpec
      });
      // prevState.notebookMetaData.push({
      //   dfName,
      // });
      return prevState;
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

  /**
   * This is a different type of visualization
   */
  addProfile(dfName: string, data: DataProps, notebookCellId: number) {
    // see if it exists
    if (this.state.profiles.filter(e => e.dfName === dfName).length > 0) {
      return;
    }
    this.setState(prevState => {
      prevState.profiles.push({
        notebookCellId,
        dfName,
        data
      });
      // prevState.notebookMetaData.push({
      //   dfName,
      //   notebookCellId,
      // });
      return prevState;
    });
  }

   onSortEnd = ({oldIndex, newIndex}: {oldIndex: number, newIndex: number}) => {
    interface ContainerState {
      notebookMetaData: MappingMetaData[];
      profiles: ProfilerInfo[];
      // TODO: refact the name `elements` --- we now have different visual elements it seems.
      elements: ContainerElementState[];
      refs: Map<string, RefObject<HTMLDivElement>>;
      // FIXME: the idToCell might not be needed given that we have refs.
      idToCell: Map<string, number>;
      // maps signals to cellIds
      reactiveCells: Map<string, number[]>;
      allReactiveCells: Set<number>;
      alerts: AlertItem[];
    }
    this.setState(prevState => {
      return {
        notebookMetaData: prevState.notebookMetaData,
        profiles: prevState.profiles,
        elements: arrayMove(prevState.elements, oldIndex, newIndex),
        refs: prevState.refs,
        idToCell: prevState.idToCell,
        reactiveCells: prevState.reactiveCells,
        allReactiveCells: prevState.allReactiveCells,
        alerts: prevState.alerts
      }
    });
  };


  render() {
    const {elements, profiles, alerts} = this.state;
    const profilerDivs = profiles.map(({dfName, data}) => (
      <Profiler
        key={dfName}
        data={data}
      />
    ));
    const chartDivs = elements.map(({notebookCellId, dfName, vegaSpec }, index) => (
      <MidasElement
        index={index}
        cellId={notebookCellId}
        key={dfName}
        dfName={dfName}
        // FIXME: title need to change
        title={dfName}
        vegaSpec={vegaSpec}
        removeChart={() => this.removeDataFrame(dfName)}
      />
    ));
    const alertDivs = alerts.map((a) => {
      const className = a.alertType === AlertType.Error ? "midas-alerts-error" : "midas-alerts-confirm";
      return <div
            className={className}
            key={`alert-${a.aId}`}
          >
            {a.msg}
        </div>;
      });
    return (
      <div id="midas-floater-container">
        <h1 className="midbar-shelf-header">
          Midas Monitor
        </h1>

        {profilerDivs}
        <MidasSortableContainer axis="xy" onSortEnd={this.onSortEnd} useDragHandle>
        {chartDivs}
        </MidasSortableContainer>
        {alertDivs}
      </div>
    );
  }
}