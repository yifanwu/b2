/// <reference path="./external/Jupyter.d.ts" />
import { MIDAS_CELL_COMM_NAME } from "./constants";
import { LogSteps, LogDebug } from "./utils";
import { AlertType } from "./types";
import { MidasSidebar } from "./components/MidasSidebar";

// types could be of: name, error, reactive
// TODO: maybe don't need these types...
// but just in case things get more complicated
type NotificationCommLoad = { type: string; style: string, value: string };
type AddSelectionLoad = { type: string; value: string };
type ReactiveCommLoad = { type: string; value: string };
type NavigateCommLoad = { type: string; value: string };
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

type MidasCommLoad = NotificationCommLoad | ReactiveCommLoad | ProfilerComm | ChartRenderComm | NavigateCommLoad | UpdateCommLoad;

/**
 * Makes the comm responsible for discovery of which visualization
 * corresponds to which cell, accomplished through inspecting the
 * metadata of the message sent.
 */
export function makeComm(refToSidebar: MidasSidebar) {
  LogSteps("makeComm");
  Jupyter.notebook.kernel.comm_manager.register_target(MIDAS_CELL_COMM_NAME,
    function (comm: any, msg: any) {
      LogDebug(`makeComm first message: ${JSON.stringify(msg)}`);
      // comm is the frontend comm instance
      // msg is the comm_open message, which can carry data
      const on_msg = make_on_msg(refToSidebar);
      refToSidebar.set_comm(comm);
      comm.on_msg(on_msg);
      comm.on_close(function (msg: any) {
        LogSteps(`CommClose`, msg);
      });
      comm.send({"test boo hoo": "great"});
    });
}


function make_on_msg(refToSidebar: MidasSidebar) {

  let refToMidas = refToSidebar.getMidasContainerRef();
  let refToProfilerShelf = refToSidebar.getProfilerShelfRef();
  let refToSelectionShelf = refToSidebar.getSelectionShelfRef();

  return function on_msg(msg: any) {
    LogSteps("on_msg", JSON.stringify(msg));
    const load = msg.content.data as MidasCommLoad;
    console.log(load.type);
    switch (load.type) {
      case "notification": {
        const errorLoad = load as NotificationCommLoad;
        LogDebug(`sending error ${errorLoad.value}`);
        const alertType = AlertType[errorLoad.style];
        refToMidas.addAlert(errorLoad.value, alertType);
        return;
      }
      case "add-selection": {
        const selectionLoad = load as AddSelectionLoad;
        refToSelectionShelf.addSelectionItem(selectionLoad.value);
        break;
      }
      case "reactive": {
        const cellId = msg.parent_header.msg_id;
        const reactiveLoad = load as ReactiveCommLoad;
        refToMidas.captureCell(reactiveLoad.value, cellId);
        refToMidas.addAlert(`Success adding cell to ${reactiveLoad.value}`, AlertType.Confirmation);
        return;
      }
      case "navigate_to_vis": {
        const navigateLoad = load as NavigateCommLoad;
        refToMidas.navigate(navigateLoad.value);
        return;
      }
      case "profiler": {
        const cellId = msg.parent_header.msg_id;
        // we are going to start the data explorers
        const dataLoad = load as ProfilerComm;
        LogSteps("Profiler", dataLoad.dfName);
        const tableName = dataLoad.dfName;
        // not sure what happened, but the data appears to have been stringified twice...
        const columnItems = JSON.parse(dataLoad.columns);
        // DataProps
        refToProfilerShelf.addOrReplaceTableItem(tableName, columnItems, cellId);
        return;
      }
      case "profiler_update_data": {
        return;
      }
      case "chart_render": {
        const cellId = msg.parent_header.msg_id;
        const chartRenderLoad = load as ChartRenderComm;
        LogSteps("Chart", chartRenderLoad.dfName);
        const spec = JSON.parse(chartRenderLoad.vega);
        refToMidas.addDataFrame(chartRenderLoad.dfName, spec, cellId);
        return;
      }
      case "chart_update_data": {
        const updateLoad = load as UpdateCommLoad;
        console.log("chart update with data");
        console.log(updateLoad.newData);
        refToMidas.replaceData(updateLoad.dfName, updateLoad.newData);
        return;
      }
    }
  };
}

