/// <reference path="./external/Jupyter.d.ts" />
import { MIDAS_CELL_COMM_NAME } from "./constants";
import { LogSteps, LogDebug } from "./utils";
import { createMidasComponent } from "./setup";
import { AlertType } from "./types";
import { MidasSidebar } from "./components/MidasSidebar";

type CommandLoad = { type: string };
type BasicLoad = { type: string; value: string };

type NotificationCommLoad = {
  type: string;
  style: string;
  value: string;
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
  vega: string;
};

type MidasCommLoad = CommandLoad | BasicLoad| NotificationCommLoad | ProfilerComm | ChartRenderComm  | UpdateCommLoad;

/**
 * Makes the comm responsible for discovery of which visualization
 * corresponds to which cell, accomplished through inspecting the
 * metadata of the message sent.
 */
export function makeComm() {
  LogSteps("makeComm");
  // refToSidebar: MidasSidebar
  Jupyter.notebook.kernel.comm_manager.register_target(MIDAS_CELL_COMM_NAME,
    function (comm: any, msg: any) {
      LogDebug(`makeComm first message: ${JSON.stringify(msg)}`);
      const set_on_msg = (onMessage: (r: MidasSidebar) => void ) => {
        comm.on_msg(onMessage);
        LogDebug("set the handler to new");
      };
      comm.on_msg((msg: any) => {
        // the first time
        const load = msg.content.data as BasicLoad;
        const midas_instance_name = load.value;
        if (load.type === "midas_instance_name") {
          const ref = createMidasComponent(midas_instance_name, comm, true);
          const on_msg = makeOnMsg(ref);
          set_on_msg(on_msg);
          // also start watching cell execution
          Jupyter.notebook.events.on("finished_execute.CodeCell", function(evt: any, data: any) {
            const code = data.cell.get_text();
            comm.send({
              command: "cell-ran",
              code,
            });
            LogDebug(`FINISHED excuting cell with code: ${code}`);
          });
        }
      });

      comm.on_close(function (msg: any) {
        LogSteps(`CommClose`, msg);
      });

      if ((window.performance) && (performance.navigation.type === 1)) {
        // Page is reloaded, use comm to make python side reconnect to the comm
        // this should be ran only once
        LogDebug("Refresh-comm called");
        // FIXME: commenting the below out because there are some infinite loops going on here...
        // comm.send({
        //   "command": "refresh-comm"
        // });
      }
    });
}


function makeOnMsg(refToSidebar: MidasSidebar) {

  let refToMidas = refToSidebar.getMidasContainerRef();
  let refToProfilerShelf = refToSidebar.getProfilerShelfRef();
  let refToSelectionShelf = refToSidebar.getSelectionShelfRef();

  return function on_msg(msg: any) {
    LogSteps("on_msg", JSON.stringify(msg));
    const load = msg.content.data as MidasCommLoad;
    console.log(load.type);
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
      case "add-selection": {
        const selectionLoad = load as BasicLoad;
        refToSelectionShelf.addSelectionItem(selectionLoad.value);
        break;
      }
      case "reactive": {
        const cellId = msg.parent_header.msg_id;
        const reactiveLoad = load as BasicLoad;
        refToMidas.captureCell(reactiveLoad.value, cellId);
        refToMidas.addAlert(`Success adding cell to ${reactiveLoad.value}`, AlertType.Confirmation);
        return;
      }
      // this is slightly awkward
      case "create_then_execute_cell": {
        // const cellId = msg.parent_header.msg_id;
        const cellLoad = load as BasicLoad;
        const c = Jupyter.notebook.insert_cell_above("code");
        c.set_text(cellLoad.value);
        c.execute();
        return;
      }
      case "navigate_to_vis": {
        const navigateLoad = load as BasicLoad;
        refToMidas.navigate(navigateLoad.value);
        return;
      }
      case "profiler": {
        const cellId = msg.parent_header.msg_id;
        // we are going to start the data explorers
        const dataLoad = load as ProfilerComm;
        LogSteps("Profiler", dataLoad.dfName);
        const tableName = dataLoad.dfName;
        const columnItems = JSON.parse(dataLoad.columns);
        // DataProps
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
        const spec = JSON.parse(chartRenderLoad.vega);
        refToMidas.addDataFrame(chartRenderLoad.dfName, spec, cellId);
        return;
      }
      case "chart_update_data": {
        const updateLoad = load as UpdateCommLoad;
        LogSteps("Chart update", updateLoad.dfName);
        console.log(updateLoad.newData);
        refToMidas.replaceData(updateLoad.dfName, updateLoad.newData);
        // also navigate
        refToMidas.navigate(updateLoad.dfName);
        return;
      }
    }
  };
}


