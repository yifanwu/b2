/// <reference path="./external/Jupyter.d.ts" />
import { MIDAS_CELL_COMM_NAME, MIDAS_RECOVERY_COMM_NAME, MIDAS_SELECTION_FUN } from "./constants";
import { LogSteps, LogDebug, LogInternalError, setupCellManagerUIChanges, getContainerFunctions, setupJupyterEvents, enableMidasInteractions, createMenuBtnGroup } from "./utils";
import { createMidasComponent } from "./setup";
import { AlertType, FunKind } from "./types";
import { MidasSidebar } from "./components/MidasSidebar";
import CellManager from "./CellManager";
import { setupLogger, LoggerFunction, LogTask, LogDataframeInteraction } from "./logging";

type CommandLoad = { type: string };
type BasicLoad = { type: string; value: string };

type InitLoad = {
  type: string; // initialize
  name: string;
  loggerId: string;
};

type ExecuteCodeLoad = {
  type: string;
  funKind: FunKind;
  code: string;
  shouldRun: boolean;
};

type ExecuteSelectionLoad = {
  type: string;
  params: string;
  dfname: string;
};

type ExecuteFunCallLoad = {
  type: string;
  funName: string;
  params: string;
};

type NotificationCommLoad  = {
  type: string;
  style: string;
  value: string;
  // note that optional might have json issues
  dfName?: string;
  columnName?: string;
};

type SynchronizeSelectionLoad = {
  type: string;
  dfName: string;
  selection: any;
};

type UpdateCommLoad = {
  type: string;
  dfName: string;
  newData: any;
  code: string;
};

type AddReactiveCell = {
  type: string;
  dfName: string;
};

type ProfilerComm = {
  type: string;
  dfName: string;
  columns: string; // decoded to ProfilerColumns
};

type ChartRenderComm = {
  type: string;
  dfName: string;
  data: string;
  encoding: string;
  code: string;
  hashVal: string;
};

type MidasCommLoad = CommandLoad
                     | BasicLoad
                     | InitLoad
                     | AddReactiveCell
                     | ExecuteFunCallLoad
                     | ExecuteCodeLoad
                     | NotificationCommLoad
                     | ProfilerComm
                     | ChartRenderComm
                     | UpdateCommLoad
                     | SynchronizeSelectionLoad
                     | ExecuteSelectionLoad;

export function openRecoveryComm() {
    const comm = Jupyter.notebook.kernel.comm_manager.new_comm(MIDAS_RECOVERY_COMM_NAME);
    LogDebug("Sending recovery message...");
    comm.send({});
}

/**
 * Makes the comm responsible for discovery of which visualization
 * corresponds to which cell, accomplished through inspecting the
 * metadata of the message sent.
 *
 * We need to keep track of whether this is first time because
 *   we do not want to add the event listen on Jupyter more than once
 *   --- the event listeners are somehow still persistent even with page refresh..
 *   Makecomm should be idempotent to page refresh.
 */
export function makeComm(is_first_time = true) {
  LogSteps("makeComm");

  Jupyter.notebook.kernel.comm_manager.register_target(MIDAS_CELL_COMM_NAME,
    function (comm: any, msg: any) {
      const set_on_msg = (onMessage: (r: MidasSidebar) => void ) => {
        comm.on_msg(onMessage);
      };

      /**
      * initialization
      * - set up cellManager
      * - set up MidasSidebar
      * - set up ProfilerShelf
      * as well as all their required comm messages and controls (e..g, to cellmanager functions)
      */
      comm.on_msg((msg: any) => {
        const load = msg.content.data as InitLoad;
        const midasInstanceName = load.name;
        const loggerId = load.loggerId;
        if (load.type !== "initialize") {
          throw LogInternalError("Should send intiialize message first!");
        }
        // modify notebook css
        const notebookDiv = document.getElementById("notebook");
        // Set Style / Append Style
        notebookDiv.style.display = "flex";
        notebookDiv.style.flexDirection = "row";
        notebookDiv.style.maxWidth = "100%";
        const notebookContainerDiv = document.getElementById("notebook-container");
        // Set Style / Append Style
        notebookContainerDiv.style.flexGrow = "1";
        notebookContainerDiv.style.marginLeft = "10pt";
        notebookContainerDiv.style.marginRight = "0pt";
        notebookContainerDiv.style.width = "10%";

        const logger = setupLogger(loggerId);
        createMenuBtnGroup();

        const cellManager = new CellManager(midasInstanceName, logger);
        const setUIItxFocus = cellManager.setFocus.bind(cellManager);
        const executeCapturedCells = cellManager.executeCapturedCells.bind(cellManager);
        setupCellManagerUIChanges(cellManager);
        const containerFunctions = getContainerFunctions(comm, logger, setUIItxFocus, executeCapturedCells);

        const columnSelectMsg = (column: string, tableName: string) => {
          const payload = {
            command: "column-selected",
            column,
            df_name: tableName,
          };
          const entry: LogDataframeInteraction = {
            action: "column_click",
            actionKind: "selection",
            dfName: tableName,
          };
          logger(entry);
          comm.send(payload);
        };


        const ref = createMidasComponent(
          columnSelectMsg,
          logger,
          containerFunctions
        );

        const on_msg = makeOnMsg(ref, cellManager, logger);
        set_on_msg(on_msg);

        if (is_first_time) {
          setupJupyterEvents(cellManager, logger);
        }
      });

      comm.on_close(function (msg: any) {
        LogSteps(`CommClose`, msg);
      });
    });
}


function makeOnMsg(refToSidebar: MidasSidebar, cellManager: CellManager, logger: LoggerFunction) {
  let refToMidas = refToSidebar.getMidasContainerRef();
  let refToProfilerShelf = refToSidebar.getProfilerShelfRef();

  return function on_msg(msg: any) {
    const load = msg.content.data as MidasCommLoad;
    switch (load.type) {
      case "notification": {
        const errorLoad = load as NotificationCommLoad;
        const alertType = AlertType[errorLoad.style];
        refToMidas.addAlert(errorLoad.value, alertType);
        if (alertType === AlertType.error && errorLoad.dfName && errorLoad.dfName !== "" && errorLoad.columnName) {
          refToProfilerShelf.markAsErrored(errorLoad.columnName, errorLoad.dfName);
        }
        return;
      }
      case "after_selection": {
        const selectionLoad = load as SynchronizeSelectionLoad;
        refToMidas.drawBrush(selectionLoad.selection);
        cellManager.runReactiveCells(selectionLoad.dfName);
        // now release
        enableMidasInteractions();
        return;
      }
      case "task-start": {
        const loggerLoad = load as BasicLoad;
        const entry: LogTask = {
          action: "task_start",
          actionKind: "task_start",
          taskId: loggerLoad.value,
        };
        logger(entry);
        return;
      }
      case "reactive": {
        const cellId = msg.parent_header.msg_id;
        const reactiveLoad = load as AddReactiveCell;
        cellManager.recordReactiveCell(reactiveLoad.dfName, cellId);
        LogDebug(`Success adding cell to ${reactiveLoad.dfName} for cell ${cellId}`);
        return;
      }
      case "deactive": {
        const cellId = msg.parent_header.msg_id;
        cellManager.removeReactiveCell(cellId);
      }
      case "execute_selection": {
        // note that this case is a special case of the execute_fun
        const selectionLoad = load as ExecuteSelectionLoad;
        cellManager.executeFunction(MIDAS_SELECTION_FUN, selectionLoad.params);
        return;
      }
      case "execute_fun": {
        const executeLoad = load as ExecuteFunCallLoad;
        cellManager.executeFunction(executeLoad.funName, executeLoad.params);
        return;
      }
      case "create_cell": {
        const cellLoad = load as ExecuteCodeLoad;
        cellManager.createCell(cellLoad.code, cellLoad.funKind, cellLoad.shouldRun);
        return;
      }
      case "profiler": {
        const cellId = msg.parent_header.msg_id;
        const dataLoad = load as ProfilerComm;
        LogSteps("Profiler", dataLoad.dfName);
        const tableName = dataLoad.dfName;
        const columnItems = JSON.parse(dataLoad.columns);
        refToProfilerShelf.addOrReplaceTableItem(tableName, columnItems, cellId);
        return;
      }

      case "chart_render": {
        const chartRenderLoad = load as ChartRenderComm;
        LogSteps("Chart", chartRenderLoad.dfName);
        const cellId = msg.parent_header.msg_id;
        const encoding = JSON.parse(chartRenderLoad.encoding);
        const data = JSON.parse(chartRenderLoad.data);
        refToMidas.addDataFrame(
          chartRenderLoad.dfName,
          encoding,
          data,
          cellId,
          chartRenderLoad.code,
          chartRenderLoad.hashVal);
        return;
      }
      case "chart_update_data": {
        // note that unlike chart_render, updates should NOT scroll!
        const updateLoad = load as UpdateCommLoad;
        refToMidas.replaceData(updateLoad.dfName, updateLoad.newData, updateLoad.code);
        return;
      }
    }
  };
}
