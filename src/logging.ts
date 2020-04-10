import { throttle } from "./utils";

export interface LogEntryBase {
  action: "coding"
  | "snapshot_single" | "snapshot_all"
  | "move_chart" | "resize_midas_area"
  | "hide_midas" | "show_midas"
  | "hide_columns_pane" | "show_columns_pane"
  | "show_chart" | "hide_chart"
  | "column_click" | "ui_selection"
  | "get_code" | "remove_df" | "navigate_to_definition_cell"
  | "hide_midas" | "show_midas"
  | "show_selection_cells" | "hide_selection_cells"
  | "navigate_to_original_cell"
  | "markdown_rendered"
  | "taskStart"
  | "scroll"
  | "new_midas_instance"
  | "view_page"
  | "leave_page";
  actionKind: "code" | "selection" | "text"
  | "uiControl" | "interaction2coding"
  | "coding2interaction" | "taskStart";
}

export interface LogCode extends LogEntryBase {
  code: string;
  cellId: string;
  cellPos: number;
}

export interface LogResize extends LogEntryBase {
  currentWidth: number;
  docWidth: number;
}

export interface LogTask extends LogEntryBase {
  taskId: string;
}

export interface LogDataframeInteraction extends LogEntryBase {
  dfName: string;
}

export interface LogSelection extends LogDataframeInteraction {
  selection: any;
}

export type LogEntry = LogCode | LogEntryBase | LogDataframeInteraction | LogResize;


export type LoggerFunction = (l: LogEntry) => void;

export function setupLogger(loggerId: string) {
  // reset
  // Jupyter.notebook.metadata.historyBackup = Jupyter.notebook.metadata.history;
  // Jupyter.notebook.metadata.history = [];

  let currentTask = "";

  if (loggerId === "") {
    // also remove existing data, but keep a temp cache just in case
    return (_: LogEntry) => {};
  }

  // set up a download function
  function downloadMidasData(print = false) {
    if (print) {
      console.log(Jupyter.notebook.metadata.history);
      return;
    } else {
      const history = JSON.stringify(Jupyter.notebook.metadata.history);
      let dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(history);
      let a = document.createElement("a");
      a.href = dataStr;
      const d = new Date();
      a.setAttribute("download", `midas_logger_${loggerId}_${d}.json`);
      a.click();
    }
  }
  (window as any).downloadMidasData = downloadMidasData;

  let lastSaved: number = null;

  function doLogEntry(newItem: LogEntry) {
    // modify state here
    if (newItem.action === "taskStart") {
      currentTask = (newItem as LogTask).taskId;
    }

    // augment with current state
    newItem["time"] = new Date();
    newItem["taskId"] = currentTask;
    newItem["loggerId"] = loggerId;

    // push
    if (Jupyter.notebook.metadata.hasOwnProperty("history")) {
      Jupyter.notebook.metadata.history.push(newItem);
    } else {
      Jupyter.notebook.metadata.history = [newItem];
    }

    const now = Date.now();
    // 10 seconds
    if ((now - lastSaved) > 10000) {
      Jupyter.notebook.save_notebook();
      lastSaved = now;
    }
  }

  // set up scroll capture
  function logScroll() {
    const entry: LogEntryBase = {
      action: "scroll",
      actionKind: "uiControl",
    };
    doLogEntry(entry);
  }
  window.addEventListener("scroll", throttle(logScroll, 3000), true);

  document.addEventListener("visibilitychange", function() {
    if (document.visibilityState === "visible") {
      const entry: LogEntryBase = {
        action: "view_page",
        actionKind: "uiControl",
      };
      doLogEntry(entry);
    } else {
      const entry: LogEntryBase = {
        action: "leave_page",
        actionKind: "uiControl",
      };
      doLogEntry(entry);
      }
  });

  const entry: LogEntryBase = {
    action: "new_midas_instance",
    actionKind: "code",
  };
  doLogEntry(entry);
  return doLogEntry;
}

