/// <reference path="./external/Jupyter.d.ts" />
import { MIDAS_CELL_COMM_NAME } from "./constants";
import { LogSteps, LogDebug, LogInternalError } from "./utils";

type MidasCommLoad = { type: string; value: string };

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
  let cellId = msg.parent_header.msg_id;
  LogSteps("on_msg", JSON.stringify(msg));
  const load = msg.content.data as MidasCommLoad;
  switch (load.type) {
    case "name": {
      LogDebug(`${load.value}, ${cellId}`);
      if (!window.hasOwnProperty("midas")) {
        LogInternalError(`midas not registered to window`);
      }
      window.midas.recordDFCellId(load.value, cellId);
    }
    case "error": {
      LogDebug(`sending error ${load.value}`);
      window.midas.showErrorMsg(load.value);
    }
  }
}