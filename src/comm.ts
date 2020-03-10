/// <reference path="./external/Jupyter.d.ts" />
import { MIDAS_CELL_COMM_NAME, MIDAS_RECOVERY_COMM_NAME, MIDAS_SELECTION_FUN } from "./constants";
import { LogSteps, LogDebug } from "./utils";
import { createMidasComponent } from "./setup";
import { AlertType, FunKind, MidasContainerFunctions } from "./types";
import { MidasSidebar } from "./components/MidasSidebar";
import CellManager from "./CellManager";

type CommandLoad = { type: string };
type BasicLoad = { type: string; value: string };

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
      comm.on_msg((msg: any) => {
        // the first time
        const load = msg.content.data as BasicLoad;
        const midasInstanceName = load.value;
        if (load.type === "midas_instance_name") {

          const columnSelectMsg = (column: string, tableName: string) => {
            const payload = {
              command: "column-selected",
              column,
              df_name: tableName,
            };
            comm.send(payload);
          };

          const addCurrentSelectionMsg = (valueStr: string) => {
            comm.send({
              "command": "add_current_selection",
              "value": valueStr
            });
          };

          const getChartCode = (dfName: string) => {
            comm.send({
              "command": "get-visualization-code-clipboard",
              "df_name": dfName
            });
          };

          // const getCode = (dfName: string) => {
          //   comm.send({
          //     "command": "get_code_clipboard",
          //     "df_name": dfName
          //   });
          // };

          const logEntry = (action: string, metadata: string) => {
            comm.send({
              "command": "log_entry",
              "action": action,
              "metadata": metadata
            });
          };

          const logEntryForResizer = (metadata: string) => {
            comm.send({
              "command": "log_entry",
              "action": "resize_midas_area",
              "metadata": metadata
            });
          };

          const removeDataFrameMsg = (dfName: string) => {
            comm.send({
              "command": "remove_dataframe",
              "df_name": dfName,
            });
          };

          const cellManager = new CellManager(midasInstanceName);
          const setUIItxFocus = cellManager.setFocus.bind(cellManager);
          const executeCapturedCells = cellManager.executeCapturedCells.bind(cellManager);

          const containerFunctions: MidasContainerFunctions = {
            removeDataFrameMsg,
            elementFunctions: {
              logEntry,
              addCurrentSelectionMsg,
              // getCode,
              setUIItxFocus,
              getChartCode,
              executeCapturedCells
            }
          };

          const ref = createMidasComponent(columnSelectMsg, logEntryForResizer, containerFunctions);
          const on_msg = makeOnMsg(ref, cellManager);
          set_on_msg(on_msg);

          // TODO: optimize and chose not to send
          if (is_first_time) {
            Jupyter.notebook.events.on("finished_execute.CodeCell", function(evt: any, data: any) {
              // we also need to tell cell manager which one was the most recently ran!
              cellManager.updateLastExecutedCell(data.cell);

              // passed to Python for more logging
              const code = data.cell.get_text();
              comm.send({
                command: "cell-ran",
                code,
              });
            });
            // this is for logging purposes
            // also need to instrument markdowncells, using "rendered.MarkdownCell" because
            // - I cannot find the creation event
            // - rendered might be a better proxy since they might change the values
            // the only issue is if the people forget to render it, oh well : /
            Jupyter.notebook.events.on("rendered.MarkdownCell", function(evt: any, data: any) {
              const code = data.cell.get_text();
              comm.send({
                command: "markdown-cell-rendered",
                code,
              });
            });
          }
        }
      });

      comm.on_close(function (msg: any) {
        LogSteps(`CommClose`, msg);
      });
    });
}


function makeOnMsg(refToSidebar: MidasSidebar, cellManager: CellManager) {

  let refToMidas = refToSidebar.getMidasContainerRef();
  let refToProfilerShelf = refToSidebar.getProfilerShelfRef();
  // let refToSelectionShelf = refToSidebar.getSelectionShelfRef();

  return function on_msg(msg: any) {
    // LogSteps("on_msg", JSON.stringify(msg));
    const load = msg.content.data as MidasCommLoad;
    switch (load.type) {
      // case "hide": {
      //   refToSidebar.hide();
      //   return;
      // }
      // case "show": {
      //   refToSidebar.show();
      //   return;
      // }
      case "notification": {
        const errorLoad = load as NotificationCommLoad;
        const alertType = AlertType[errorLoad.style];
        refToMidas.addAlert(errorLoad.value, alertType);
        return;
      }
      case "after_selection": {
        const selectionLoad = load as SynchronizeSelectionLoad;
        refToMidas.drawBrush(selectionLoad.selection);
        cellManager.runReactiveCells(selectionLoad.dfName);
        return;
      }
      // case "add_selection_to_shelf": {
      //   const selectionLoad = load as BasicLoad;
      //   refToSelectionShelf.addSelectionItem(selectionLoad.value);
      //   refToMidas.drawBrush(selectionLoad.value);
      //   break;
      // }
      case "reactive": {
        const cellId = msg.parent_header.msg_id;
        const reactiveLoad = load as AddReactiveCell;
        cellManager.recordReactiveCell(reactiveLoad.dfName, cellId);
        LogDebug(`Success adding cell to ${reactiveLoad.dfName} for cell ${cellId}`);
        return;
      }
      case "execute_selection": {
        // note that this case is a special case of the execution
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
        // const cellId = msg.parent_header.msg_id;
        const cellLoad = load as ExecuteCodeLoad;
        cellManager.createCell(cellLoad.code, cellLoad.funKind, cellLoad.shouldRun);
        return;
      }
      case "navigate_to_vis": {
        const navigateLoad = load as BasicLoad;
        refToMidas.navigate(navigateLoad.value);
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
      case "profiler_update_data": {
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
        const updateLoad = load as UpdateCommLoad;
        refToMidas.replaceData(updateLoad.dfName, updateLoad.newData, updateLoad.code);
        // really bad idea here to scroll: causes instability of viewing!
        // refToMidas.navigate(updateLoad.dfName);
        return;
      }
    }
  };
}
