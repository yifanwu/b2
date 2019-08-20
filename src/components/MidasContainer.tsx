import React from "react";

import MidasElement from "./MidasElement";
import { hashCode } from "../utils";

interface ContainerElementState {
  id: number;
  name: string;
  fixYScale: () => void;
}

interface ContainerState {
    elements: ContainerElementState[];
    idToCell: Map<string, number>;
    alerts: string[];
}

/**
 * Container for the MidasElements that hold the visualization.
 */
export default class MidasContainer extends React.Component<any, ContainerState> {
    constructor(props?: any) {
      super(props);
      this.state = {
        elements: [],
        idToCell: new Map(),
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

    showErrorMsg(msg: string) {
      // make this disappearing
      this.setState(prevState => {
        prevState.alerts.push(msg);
        return prevState;
      });
      window.setTimeout(() => {
        this.setState(prevState => {
          const alerts = prevState.alerts.filter(a => a !== msg);
          return {
            alerts
          };
        });
      }, 2000);
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
       console.log("State " + JSON.stringify(this.state));
    }

    /**
     * Removes the given data frame via id
     * @param key the id of the data frame
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
          id={id}
          key={id}
          name={name}
          onClick={() => this.removeDataFrame(id)}
          getCellId={() => this.getCellId(name)}
          fixYScale={() => fixYScale()} />
      ));
      const alertDivs = this.state.alerts.map((a) => <div
          className="midas-alerts"
          key={`alert-${hashCode(a)}`}
        >
          {a}
        </div>);
      return (
        <div id="midas-floater-container">
          {elements}
          {alertDivs}
        </div>
      );
    }
  }