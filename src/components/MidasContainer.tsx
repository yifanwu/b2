import React, { RefObject } from "react";
import arrayMove from "array-move";

import { CloseButton } from "./CloseButton";
import { EncodingSpec } from "../charts/vegaGen";
import { AlertType, MidasContainerFunctions, SelectionValue } from "../types";
import { LogInternalError, LogSteps, getDfId, LogDebug, addNotebookMenuBtn } from "../utils";
import { SNAPSHOT_BUTTON, MIDAS_CONTAINER_ID } from "../constants";

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
  code: string;
  hashVal: string;
}

interface AlertItem {
  msg: string;
  alertType: AlertType;
  shown: boolean;
}

interface ContainerProps {
  containerFunctions: MidasContainerFunctions;
}

interface ContainerState {
  elements: ContainerElementState[];
  refs: Map<string, RefObject<HTMLDivElement>>;
  idToCell: Map<string, number>;
  alerts: AlertItem[];
  midasPythonInstanceName: string;
}

// const MidasSortableContainer = SortableContainer(({ children }: { children: any }) => {
//   return <div>{children}</div>;
// }, {withRef: true});

/**
 * Container for the MidasElements that hold the visualization.
 */
export default class MidasContainer extends React.Component<ContainerProps, ContainerState> {

  refsCollection = {};

  constructor(props?: ContainerProps) {
    super(props);
    this.addAlert = this.addAlert.bind(this);
    this.drawBrush = this.drawBrush.bind(this);
    this.removeAlert = this.removeAlert.bind(this);
    this.snapShotAll = this.snapShotAll.bind(this);

    addNotebookMenuBtn(
      this.snapShotAll,
      SNAPSHOT_BUTTON,
      "📷 charts",
      "Take a snapshot of current charts"
    );

    this.state = {
      elements: [],
      refs: new Map(),
      idToCell: new Map(),
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

  async snapShotAll() {
    // go to the uncollapsed children elements, get the svgs and put in one paths
    // iterate through this
    let allSvgStrs: string[] = [];
    let allCodeStrs: string[] = [];
    for (let key in this.refsCollection) {
      const element = this.refsCollection[key];
      if (element) {
        const svg = await element.getSvg();
        allSvgStrs.push(svg);
        const code = element.getCode();
        allCodeStrs.push(`# ${code}`);
      }
      // try {
      // } catch (err) {
      //   LogInternalError(`Cannot create svg for element, with error: ${err}`);
      // }
    }
    const combined = allSvgStrs.join("");
    const comments = "# Current snapshot queries:\n" + allCodeStrs.join("\n");
    // this bleads the abstraction a little
    this.props.containerFunctions.elementFunctions.executeCapturedCells(`<div>${combined}<div>`, comments);
    this.props.containerFunctions.elementFunctions.logEntry("snapshot_all", "");
  }

  drawBrush(selectionArrayStr: string) {
    const selectionArray = JSON.parse(selectionArrayStr);
    // note that the below is actually not an array, but an empty string
    // the empty string is differnt from epty array in that the brush need to be actively deselected
    if (selectionArray.length === 0) {
      for (let e of this.state.elements) {
        this.refsCollection[e.dfName].updateSelectionMarks({});
      }
      return;
    }

    const dfNames = selectionArray.map((s: any) => Object.keys(s)[0]) as string[];
    // FIXME: iterate through dfNames as opposed elements
    for (let e of this.state.elements) {
      const idx = dfNames.findIndex((v) => v === e.dfName);
      if (idx > -1) {
        const selectionItem = selectionArray[idx] as SelectionValue;
        this.refsCollection[e.dfName].updateSelectionMarks(selectionItem[e.dfName]);
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

  navigate(dfName: string) {
    const ele = document.getElementById(getDfId(dfName));
    ele.scrollIntoView({behavior: "smooth"});
  }


  addAlert(msg: string, alertType: AlertType = AlertType.error) {
    // const idx = this.state.alerts.length;
    this.setState(prevState => {
      prevState.alerts.push({
        msg,
        alertType,
        shown: true,
      });
      return prevState;
    });
    // if (alertType === AlertType.Confirmation) {
    //   const self = this;
    //   window.setTimeout(() => {
    //     self.removeAlert(idx);
    //   }, ALERT_ALIVE_TIME);
    // }
  }

  removeAlert(idx: number) {
    this.setState(prevState => {
      prevState.alerts[idx].shown = false;
      return prevState;
    });
  }


  resetState() {
    // TODO
    throw Error("not implemented");
  }


  /**
   * Adds the visualization of the given data frame to this container
   * @param id the id of the data frame
   * @param dfName the name of the data frame
   * @param hashVal python side generated parameter for hashing
   */
  addDataFrame(dfName: string, encoding: EncodingSpec, data: any[], notebookCellId: string, code: string, hashVal: string) {
    this.setState(prevState => {
      // see if we need to delete the old one first
      const idx = prevState.elements.findIndex((v) => v.dfName === dfName);
      const newElement = {
        notebookCellId,
        dfName,
        encoding,
        data,
        changeStep: 1,
        code,
        hashVal
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

  replaceData(dfName: string, data: any[], code: string) {
    this.refsCollection[dfName].replaceData(data, code);
  }


  /**
   * Removes the given data frame via id
   * @param key the id of the data frame
   */
  removeDataFrame(dfName: string) {
    this.props.containerFunctions.removeDataFrameMsg(dfName);
    // should also remove ref otherwise snapshot will bug out
    delete this.refsCollection[dfName];
    this.setState(prevState => {
      return {
        elements: prevState.elements.filter(e => (e.dfName !== dfName))
      };
    });
  }

  // onSortEnd = ({ oldIndex, newIndex }: { oldIndex: number, newIndex: number }) => {
  //   this.setState(prevState => {
  //     return {
  //       notebookMetaData: prevState.notebookMetaData,
  //       elements: arrayMove(prevState.elements, oldIndex, newIndex),
  //       refs: prevState.refs,
  //       idToCell: prevState.idToCell,
  //       alerts: prevState.alerts
  //     };
  //   });
  // }

  moveElement(oldIndex: number) {
    return (direction: "left" | "right") => {
      let newIndex = oldIndex + 1;
      if (direction === "left") {
        newIndex = oldIndex - 1;
      }
      // FIXME: bound the max and the min

      this.setState(prevState => {
        return {
          elements: arrayMove(prevState.elements, oldIndex, newIndex),
          refs: prevState.refs,
          idToCell: prevState.idToCell,
          alerts: prevState.alerts
        };
      });
    };
  }


  render() {
    const { elements, alerts } = this.state;
    const chartDivs = elements.map(({
      notebookCellId, dfName, data, encoding, changeStep, code, hashVal }, index) => {
      return <MidasElement
        ref={r => this.refsCollection[dfName] = r}
        moveElement={this.moveElement(index)}
        functions={this.props.containerFunctions.elementFunctions}
        cellId={notebookCellId}
        key={`${dfName}-${hashVal}`}
        dfName={dfName}
        title={dfName}
        encoding={encoding}
        code={code}
        data={data}
        changeStep={changeStep}
        removeChart={() => this.removeDataFrame(dfName)}
      />;
    });
    const alertDivs = [];
    for (let i = 0; i < alerts.length; i++) {
      const a = alerts[i];
      if (a.shown) {
        const className = a.alertType === AlertType.error
        ? "midas-alerts-error"
        : "midas-alerts-debug";
        const newDiv = <div
          className={`midas-alert ${className}`}
        >
        <CloseButton
          onClick={() => this.removeAlert(i)}
          size={15}
          color={"white"}
          paddingRight={5}
        />
        {a.msg}
      </div>;
        alertDivs.push(newDiv);
      }
    }
    // const content = (chartDivs.length > 0) ?
    //   <MidasSortableContainer
    //     axis="xy"
    //     onSortEnd={this.onSortEnd}
    //     useDragHandle
    //   >{chartDivs}</MidasSortableContainer>
    //   : <ChartsViewLandingPage/>;
    const content = (chartDivs.length > 0) ? chartDivs : <ChartsViewLandingPage />;
    const cssHack = <div style={{height: 200}}></div>;
    return (
      <div className="shelf" id={MIDAS_CONTAINER_ID}>
        <div id="midas-alert-area">
          {alertDivs}
        </div>
        {content}
        {cssHack}
      </div>
    );
  }
}
