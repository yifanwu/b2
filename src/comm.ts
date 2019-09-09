/// <reference path="./external/Jupyter.d.ts" />
import { MIDAS_CELL_COMM_NAME } from "./constants";
import { LogSteps, LogDebug, LogInternalError } from "./utils";
import { AlertType } from "./types";

// types could be of: name, error, reactive
// TODO: maybe don't need these types...
type ErrorCommLoad = { type: string; value: string };
type CreateCommLoad = { type: string; value: string };
type ReactiveCommLoad = { type: string; value: string};
type MidasCommLoad = ErrorCommLoad | CreateCommLoad | ReactiveCommLoad;

/**
 * Makes the comm responsible for discovery of which visualization
 * corresponds to which cell, accomplished through inspecting the
 * metadata of the message sent.
 */
export function makeComm() {
  console.log("Making comm.")
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
  // TODO: add error checking in the payload to give more eager/intuitive warning
  let cellId = msg.parent_header.msg_id;
  LogSteps("on_msg", JSON.stringify(msg));
  const load = msg.content.data as MidasCommLoad;

  switch (load.type) {
    case "name": {
      const nameLoad = load as CreateCommLoad;
      LogDebug(`${nameLoad.value}, ${cellId}`);
      if (!window.hasOwnProperty("midas")) {
        LogInternalError(`midas not registered to window`);
      }
      window.midas.recordDFCellId(nameLoad.value, cellId);
    }
    case "error": {
      const errorLoad = load as ErrorCommLoad;
      LogDebug(`sending error ${errorLoad.value}`);
      window.midas.addAlert(errorLoad.value);
    }
    case "reactive": {
      const reactiveLoad = load as ReactiveCommLoad;
      window.midas.captureCell(reactiveLoad.value, cellId);
      window.midas.addAlert(`Success adding cell to ${reactiveLoad.value}`, AlertType.Confirmation);
    }
  }
}