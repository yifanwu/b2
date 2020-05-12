import { throttle } from "./utils";

export type ActionKind = "code" | "ui_support_code"
| "selection" | "text"
| "ui_control" | "interaction2coding"
| "coding2interaction" | "task_start";

export interface LogEntryBase {
  action: "coding"
  | "typing"
  | "snapshot_single" | "snapshot_all"
  | "move_chart" | "resize_midas_area"
  | "hide_base_data" | "show_base_data"
  | "hide_columns_pane" | "show_columns_pane"
  | "show_chart" | "hide_chart"
  | "column_click" | "ui_selection"
  | "get_code" | "remove_df" | "navigate_to_definition_cell"
  | "hide_midas" | "show_midas"
  | "show_selection_cells" | "hide_selection_cells"
  | "navigate_to_original_cell"
  | "markdown_rendered"
  | "task_start"
  | "scroll"
  | "new_midas_instance"
  | "view_page"
  | "leave_page";
  actionKind: ActionKind;
}

export interface LogKeyStroke extends LogEntryBase {
  keyStroke: string;
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
    if (newItem.action === "task_start") {
      currentTask = (newItem as LogTask).taskId;
    }

    // augment with current state
    newItem["time"] = new Date();
    newItem["taskId"] = currentTask;
    newItem["loggerId"] = loggerId;

    // process code
    if (newItem.action === "coding") {
      const actionKind = getActionKindFromCode((newItem as LogCode).code);
      newItem["actionKind"] = actionKind;
    }

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
      actionKind: "ui_control",
    };
    doLogEntry(entry);
  }

  function logTyping(event: any) {
    const entry: LogKeyStroke = {
      action: "typing",
      actionKind: "code",
      keyStroke: String.fromCharCode(event.keyCode)
    };
    doLogEntry(entry);
  }
  window.addEventListener("scroll", throttle(logScroll, 3000), true);
  window.addEventListener("keydown", logTyping, true);

  document.addEventListener("visibilitychange", function() {
    if (document.visibilityState === "visible") {
      const entry: LogEntryBase = {
        action: "view_page",
        actionKind: "ui_control",
      };
      doLogEntry(entry);
    } else {
      const entry: LogEntryBase = {
        action: "leave_page",
        actionKind: "ui_control",
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


function getActionKindFromCode(code: string): ActionKind {
  const history = Jupyter.notebook.metadata.history;
  if (code.includes("display(HTML(")) {
    // already logged in the UI interaction
    return "ui_support_code";
  }
  const itx2code = [
    ".get_filtered_data",
    ".current_selection",
    ".immediate_interaction_value",
    ".immediate_interaction",
    ".all_selections",
    "%%reactive"
  ];
  for (let i of itx2code) {
    if (code.includes(i)) {
      return "interaction2coding";
    }
  }
  if (code.includes(".sel([")) {
    // if prev action was "ui_selection"
    const len = history.length;
    const prevAction = history[len - 1].action;
    if (( prevAction === "ui_selection") || (prevAction === "remove_df")) {
      return "ui_support_code";
    }
    return "coding2interaction";
  }
  if (code.includes(".vis(")) {
    const len = history.length;
    if (history[len - 1].action === "column_click") {
      return "ui_support_code";
    }
    // sometimes there is a scroll if the cell has been created before
    if ((len > 1)
      && (history[len - 2].action === "column_click")
      && (history[len - 1].action === "scroll")) {
        return "ui_support_code";
    }
    return "coding2interaction";
  }
  return "code";
}