import React from "react";

import MidasElement from "./MidasElement";
import { hashCode, LogInternalError, LogSteps } from "../utils";
import { AlertType } from "../types";
import {
  SortableContainer,
  SortableElement,
  SortableHandle,
} from 'react-sortable-hoc';

interface ContainerElementState {
  id: number;
  name: string;
  fixYScale: () => void;
}
import arrayMove from 'array-move';

interface AlertItem {
  msg: string;
  alertType: AlertType;
  aId: number;
}

interface ContainerState {
    elements: ContainerElementState[];
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
      this.tick = this.tick.bind(this);
      this.captureCell = this.captureCell.bind(this);

      // NOTE: maybe other binds needed as well...
      this.state = {
        elements: [],
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
      console.log(
        `Recording the dataframe ${name} was defined at ${cell}`
      );
      
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
      this.setState({
          elements: [],
          idToCell: new Map(),
          reactiveCells: new Map(),
          allReactiveCells: new Set(),
          alerts: []
      });
    }

    /**
     * Adds the visualization of the given data frame to this container
     * @param id the id of the data frame
     * @param dfName the name of the data frame
     */
    addDataFrame(id: number, dfName: string, fixYScale: () => void, cb: () => void) {
      let shouldReturn = false;
      // todo: make less janky/more idiomatic?
      this.state.elements.forEach((e) => {
        if (id === e.id) {
          shouldReturn = true;
        }
      });

      if (shouldReturn) return;

      this.setState(prevState => {
        prevState.elements.push({
          id: id,
          name: dfName,
          fixYScale: fixYScale,
        });
        return prevState;
       }, cb);
    }

    onSortEnd = ({oldIndex, newIndex}: {oldIndex: number, newIndex: number}) => {
      this.setState(prevState => {
        return {
          elements: arrayMove(prevState.elements, oldIndex, newIndex),
          idToCell: prevState.idToCell,
          reactiveCells: prevState.reactiveCells,
          allReactiveCells: prevState.allReactiveCells,
          alerts: prevState.alerts
        }
      });
    };
  
    /**
     * Removes the given data frame via id
     * @param id the id of the data frame
     */
    removeDataFrame(id: number) {
      this.setState(prevState => {
        return {
          elements: prevState.elements.filter(e => (e.id !== id))
        };
      });
    }

    render() {
      const elements = this.state.elements.map(({ id, name, fixYScale }, index) => (
        <MidasElement
          index={index}
          id={id}
          key={id}
          name={name}
          onClick={() => this.removeDataFrame(id)}
          getCellId={() => this.getCellId(name)}
          fixYScale={() => fixYScale()} />
      ));
      const alertDivs = this.state.alerts.map((a) => {
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
          <MidasSortableContainer onSortEnd={this.onSortEnd} useDragHandle>
            {elements}
          </MidasSortableContainer>
          {alertDivs}
        </div>
      );
    }
  }