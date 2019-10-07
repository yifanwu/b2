/// <reference path="./external/Jupyter.d.ts" />
import { MIDAS_CELL_COMM_NAME } from "./constants";
import { LogSteps, LogDebug, LogInternalError } from "./utils";
import { AlertType } from "./types";
import { Spec, View } from "vega";
import { DataProps } from "@nteract/data-explorer/src/types";

// TODO: maybe don't need these types...
// but just in case things get more complicated
type ErrorCommLoad = { type: string; value: string };
type ReactiveCommLoad = { type: string; value: string };
type NavigateCommLoad = { type: string; value: string };
type ProfilerComm = {
  type: string;
  dfName: string;
  data: DataProps;
};
type ChartRenderComm = {
  type: string;
  dfName: string;
  vega: Spec
};

type MidasCommLoad = ErrorCommLoad | ReactiveCommLoad | ProfilerComm | ChartRenderComm | NavigateCommLoad;

/**
 * Makes the comm responsible for discovery of which visualization
 * corresponds to which cell, accomplished through inspecting the
 * metadata of the message sent.
 */
export function makeComm() {
  Jupyter.notebook.kernel.comm_manager.register_target(MIDAS_CELL_COMM_NAME,
    function (comm: any, msg: any) {
      // comm is the frontend comm instance
      // msg is the comm_open message, which can carry data

      // Register handlers for later messages:
      comm.on_msg(on_msg);
      comm.on_close(function (msg: any) { });
    });
}

function on_msg(msg: any) {
  // need to make sure that midas is loaded
  if (!window.hasOwnProperty("midas")) {
    LogInternalError(`midas not registered to window`);
  }
  LogSteps("on_msg", JSON.stringify(msg));
  const load = msg.content.data as MidasCommLoad;
  switch (load.type) {
    case "error": {
      const errorLoad = load as ErrorCommLoad;
      LogDebug(`sending error ${errorLoad.value}`);
      window.midas.addAlert(errorLoad.value);
    }
    case "reactive": {
      const cellId = msg.parent_header.msg_id;
      const reactiveLoad = load as ReactiveCommLoad;
      window.midas.captureCell(reactiveLoad.value, cellId);
      window.midas.addAlert(`Success adding cell to ${reactiveLoad.value}`, AlertType.Confirmation);
    }
    case "navigate_to_vis": {
      const navigateLoad = load as NavigateCommLoad;
      window.midas.navigate(navigateLoad.value);
    }
    case "profiler": {
      const cellId = msg.parent_header.msg_id;
      // we are going to start the data explorers
      const dataLoad = load as ProfilerComm;
      window.midas.addProfile(dataLoad.dfName, dataLoad.data, cellId);
    }
    case "profiler_update_data": {

    }
    case "chart_render": {
      const cellId = msg.parent_header.msg_id;
      const chartRenderLoad = load as ChartRenderComm;
      window.midas.addDataFrame(chartRenderLoad.dfName, chartRenderLoad.vega, cellId);
    }
    case "chart_update_data": {

    }
  }
}