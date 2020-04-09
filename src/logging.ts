
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
  | "taskStart";
  actionKind: "code" | "selection" | "text"
  | "uiControl" | "interaction2coding"
  | "coding2interaction" | "taskStart";
  time: Date;
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
  if (loggerId === "") {
    return (_: LogEntry) => {};
  }
  function downloadMidasData() {
    const history = JSON.stringify(Jupyter.notebook.metadata.history);
    let dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(history);
    let a = document.createElement("a");
    a.href = dataStr;
    const d = new Date();
    a.setAttribute("download", `midas_logger_${loggerId}_${d}.json`);
    a.click();
  }

  (window as any).downloadMidasData = downloadMidasData;

  return (newItem: LogEntry) => {
    if (Jupyter.notebook.metadata.hasOwnProperty("history")) {
      Jupyter.notebook.metadata.history.push(newItem);
    } else {
      Jupyter.notebook.metadata.history = [newItem];
    }
    Jupyter.notebook.save_notebook();
  };
}

