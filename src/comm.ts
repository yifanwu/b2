/// <reference path="./external/Jupyter.d.ts" />
import { MIDAS_CELL_COMM_NAME, MIDAS_RECOVERY_COMM_NAME, MIDAS_SELECTION_FUN } from "./constants";
import { LogSteps, LogDebug } from "./utils";
import { createMidasComponent } from "./setup";
import { AlertType, MidasContainerFunctions } from "./types";
import { MidasSidebar } from "./components/MidasSidebar";
import CellManager, { FunKind }  from "./CellManager";

type CommandLoad = { type: string };
type BasicLoad = { type: string; value: string };

type ExecuteCodeLoad = {
  type: string;
  funKind: FunKind;
  code: string;
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
};

type MidasCommLoad = CommandLoad
                     | BasicLoad
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
              "command": "get_visualization_code_clipboard",
              "df_name": dfName
            });
          };

          const getCode = (dfName: string) => {
            comm.send({
              "command": "get_code_clipboard",
              "df_name": dfName
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
              addCurrentSelectionMsg,
              getCode,
              setUIItxFocus,
              getChartCode,
              executeCapturedCells
            }
          };

          const ref = createMidasComponent(columnSelectMsg, containerFunctions);
          const on_msg = makeOnMsg(ref, cellManager);
          set_on_msg(on_msg);

          if (is_first_time) {
            Jupyter.notebook.events.on("finished_execute.CodeCell", function(evt: any, data: any) {
              // we also need to tell cell manager which one was the most recently ran!
              const code = data.cell.get_text();
              comm.send({
                command: "cell-ran",
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
      case "hide": {
        refToSidebar.hide();
        return;
      }
      case "show": {
        refToSidebar.show();
        return;
      }
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
        const reactiveLoad = load as BasicLoad;
        cellManager.captureCell(reactiveLoad.value, cellId);
        LogDebug(`Success adding cell to ${reactiveLoad.value} for cell ${cellId}`);
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
      case "create_then_execute_cell": {
        // const cellId = msg.parent_header.msg_id;
        const cellLoad = load as ExecuteCodeLoad;
        cellManager.createCellAndExecute(cellLoad.code, cellLoad.funKind);
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
        refToMidas.addDataFrame(chartRenderLoad.dfName, encoding, data, cellId);
        return;
      }
      case "chart_update_data": {
        const updateLoad = load as UpdateCommLoad;
        refToMidas.replaceData(updateLoad.dfName, updateLoad.newData);
        refToMidas.navigate(updateLoad.dfName);
        return;
      }
    }
  };
}
