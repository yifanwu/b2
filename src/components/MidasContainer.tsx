import React, { RefObject } from "react";

import MidasElement from "./MidasElement";
import Profiler from "./Profiler";
import { hashCode, LogInternalError, LogSteps } from "../utils";
import { AlertType } from "../types";
import {
  SortableContainer,
} from "react-sortable-hoc";
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
  newData?: any[];
  chanageStep: number;
}

interface ProfilerInfo {
  dfName: string;
  notebookCellId: number;
  data: DataProps;
}

import arrayMove from "array-move";

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
  comm: any; // unfortunately not typed
}

const ALERT_ALIVE_TIME = 5000;

const MidasSortableContainer = SortableContainer(({children}: {children: any}) => {
  return <div>{children}</div>;
});

/**
 * Container for the MidasElements that hold the visualization.
 */
export default class MidasContainer extends React.Component<{}, ContainerState> {
  // refLookup: Map<string, typeof MidasElement>;

  constructor(props?: {}) {
    super(props);

    // NOTE: maybe other binds needed as well...
    this.tick = this.tick.bind(this);
    this.captureCell = this.captureCell.bind(this);
    this.addAlert = this.addAlert.bind(this);
    this.closeAlert = this.closeAlert.bind(this);
    // this.refLookup = new Map();

    this.state = {
      comm: null,
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


  set_comm(comm: any) {
    this.setState({comm});
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
    if (alertType === AlertType.Confirmation) {
      window.setTimeout(() => {
        this.closeAlert(aId);
      }, ALERT_ALIVE_TIME);
    }
  }

  closeAlert(aId: number) {
    return () => {
      this.setState(prevState => {
        const alerts = prevState.alerts.filter(a => a.aId !== aId);
        return {
          alerts
        };
      });
    };
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
    console.log(`Adding data frame: ${dfName} associated with cell ${notebookCellId}`);
    if (this.state.elements.filter(e => e.dfName === dfName).length > 0) {
      return;
    }

    this.setState(prevState => {
      prevState.elements.push({
        notebookCellId,
        dfName,
        vegaSpec,
        chanageStep: 1
      });
      // prevState.notebookMetaData.push({
      //   dfName,
      // });
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
          e.chanageStep = e.chanageStep + 1;
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
      };
    });
  }

  // setMidasElementRef(dfName: string) {
  //   return (ref: typeof MidasElement) => {
  //     this.refLookup[dfName] = ref;
  //   };
  // }

  render() {
    const { comm, elements, profiles, alerts } = this.state;
    const profilerDivs = profiles.map(({dfName, data}) => (
      <Profiler
        key={dfName}
        dfName={dfName}
        data={data}
      />
    ));
    const chartDivs = elements.map(({notebookCellId, dfName, vegaSpec }, index) => {
      // const ref = this.setMidasElementRef(dfName);
      return <MidasElement
        index={index}
        cellId={notebookCellId}
        key={dfName}
        dfName={dfName}
        comm={comm}
        tick={this.tick}
        // FIXME: title need to change
        title={dfName}
        vegaSpec={vegaSpec}
        // ref={ref}
        // ref={(r) => this.setMidasElementRef(dfName, r)}
        removeChart={() => this.removeDataFrame(dfName)}
      />;
    });
    const alertDivs = alerts.map((a, i) => {
      const close = this.closeAlert(a.aId);
      const className = a.alertType === AlertType.Error ? "midas-alerts-error" : "midas-alerts-debug";
      return <div
            className={className}
            key={`alert-${a.aId}`}
          >
            {a.msg}
            <button className="notification-btn" onClick={close}>x</button>
        </div>;
      });
    return (
      <div id="midas-floater-container">
        <div className="midbar-shelf-header">
          Midas Monitor
        </div>

        {profilerDivs}
        <MidasSortableContainer axis="xy" onSortEnd={this.onSortEnd} useDragHandle>
        {chartDivs}
        </MidasSortableContainer>
        {alertDivs}
      </div>
    );
  }
}