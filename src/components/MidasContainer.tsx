import React, { RefObject } from "react";
import arrayMove from "array-move";
import { SortableContainer } from "react-sortable-hoc";

import { EncodingSpec } from "../charts/vegaGen";
import { ALERT_ALIVE_TIME } from "../constants";
import { AlertType, MidasContainerFunctions, SelectionValue } from "../types";
import { LogInternalError, LogSteps, getDfId, LogDebug } from "../utils";

import { ChartsViewLandingPage } from "./ChartsViewLangingPage";
import MidasElement from "./MidasElement";

// Mappings
//  this stores the information connecting the cells to
//  we want thtis to be both directions.
interface MappingMetaData {
  dfName: string;
}

// TODO: we need to re
interface ContainerElementState {
  dfName: string;
  notebookCellId: string;
  encoding: EncodingSpec;
  data: any[];
  changeStep: number;
}

interface AlertItem {
  msg: string;
  alertType: AlertType;
  aId: number;
}

interface ContainerProps {
  containerFunctions: MidasContainerFunctions;
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


const MidasSortableContainer = SortableContainer(({ children }: { children: any }) => {
  return <div>{children}</div>;
});

/**
 * Container for the MidasElements that hold the visualization.
 */
export default class MidasContainer extends React.Component<ContainerProps, ContainerState> {

  refsCollection = {};

  constructor(props?: ContainerProps) {
    super(props);
    this.tick = this.tick.bind(this);
    this.captureCell = this.captureCell.bind(this);
    this.addAlert = this.addAlert.bind(this);
    this.drawBrush = this.drawBrush.bind(this);

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


  drawBrush(selectionArrayStr: string) {
    const selectionArray = JSON.parse(selectionArrayStr);
    // note that the below is actually not an array, but an empty string
    // the empty string is differnt from epty array in that the brush need to be actively deselected
    if (selectionArray.length === 0) {
      for (let e of this.state.elements) {
        this.refsCollection[e.dfName].drawBrush({});
      }
      return;
    }

    const dfNames = selectionArray.map((s: any) => Object.keys(s)[0]) as string[];
    for (let e of this.state.elements) {
      const idx = dfNames.findIndex((v) => v === e.dfName);
      if (idx > -1) {
        const selectionItem = selectionArray[idx] as SelectionValue;
        this.refsCollection[e.dfName].drawBrush(selectionItem[e.dfName]);
      }
    }
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
    const cells = this.state.reactiveCells.get(dfName);
    function getCell(c: number) {
      const cIdxMsg = Jupyter.notebook.get_msg_cell(c);
      if (cIdxMsg) {
        const idx = Jupyter.notebook.find_cell_index(cIdxMsg);
        if (idx > -1) {
          LogDebug(`Found cell for ${dfName} with ${c}`);
          return idx;
        }
      }
      LogDebug(`One of the cells is no longer found for ${c}`);
    }
    if (cells) {
      let cellIdxs = [];
      for (let i = 0; i < cells.length; i ++) {
        const r = getCell(cells[i]);
        if (r) {
          cellIdxs.push(r);
        } else {
          // remove if they are no longer available
          cells.splice(i, 1);
        }
      }
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
    const elmnt = document.getElementById(getDfId(dfName));
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
      self.setState(p => {
        return { alertCounter: p.alertCounter + 1 };
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
  addDataFrame(dfName: string, encoding: EncodingSpec, data: any[], notebookCellId: string) {
    this.setState(prevState => {
      // see if we need to delete the old one first
      const idx = prevState.elements.findIndex((v) => v.dfName === dfName);
      const newElement = {
        notebookCellId,
        dfName,
        encoding,
        data,
        changeStep: 1
      };
      if (idx > -1) {
        // here we are replacing the value
        prevState.elements[idx] = newElement;
      } else {
        // LogDebug(`Adding data frame: ${dfName} associated with cell ${notebookCellId}`);
        prevState.elements.push(newElement);
      }
      return prevState;
    });
  }

  addBrush(dfName: string, selection: any) {
    this.refsCollection[dfName].addBrush(selection);
  }

  replaceData(dfName: string, data: any[]) {
    this.refsCollection[dfName].replaceData(data);
  }


  /**
   * Removes the given data frame via id
   * @param key the id of the data frame
   */
  removeDataFrame(dfName: string) {
    this.props.containerFunctions.removeDataFrameMsg(dfName);

    this.setState(prevState => {
      return {
        elements: prevState.elements.filter(e => (e.dfName !== dfName))
      };
    });
  }

  onSortEnd = ({ oldIndex, newIndex }: { oldIndex: number, newIndex: number }) => {
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
      notebookCellId, dfName, data, encoding, changeStep: chanageStep }, index) => {
      return <MidasElement
        ref={r => { this.refsCollection[dfName] = r; }}
        functions={this.props.containerFunctions.elementFunctions}
        cellId={notebookCellId}
        key={`${dfName}-${encoding.mark}-${encoding.x}-${encoding.y}`}
        dfName={dfName}
        tick={this.tick}
        title={dfName}
        encoding={encoding}
        data={data}
        changeStep={chanageStep}
        removeChart={() => this.removeDataFrame(dfName)}
      />;
    });
    const alertDivs = [];
    for (let i = alertCounter; i < alerts.length; i++) {
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
    // const content = (chartDivs.length > 0) ? <MidasSortableContainer axis="xy" onSortEnd={this.onSortEnd} useDragHandle>{chartDivs}</MidasSortableContainer> : <ChartsViewLandingPage/>;
    const content = (chartDivs.length > 0) ? chartDivs : <ChartsViewLandingPage />;
    return (
      <div className="shelf" id="midas-floater-container">
        {content}
        {alertDivs}
      </div>
    );
  }
}
