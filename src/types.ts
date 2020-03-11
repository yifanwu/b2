export enum AlertType {
  Error = "error",
  Debug = "debug",
  Confirmation = "confirmation"
}

// the index is the column names, corresponding to values
// even if it's a single value, we will just wrap it in an array
export type SelectionValue = number[] | string[];
export type PerChartSelectionValue = {[index: string]: SelectionValue};

export interface MidasElementFunctions {
  addCurrentSelectionMsg: (valueStr: string) => void;
  logEntry: (action: string, metadata: string) => void;
  // getCode: (dataFrame: string) => void;
  setUIItxFocus: (dataFrame?: string) => void;
  getChartCode: (dataFrame: string) => void;
  executeCapturedCells: (svg: string, comments: string) => void;
}

export interface MidasContainerFunctions {
  removeDataFrameMsg: (dataFrame: string) => void;
  elementFunctions: MidasElementFunctions;
}

export type FunKind = "chart" | "query" | "interaction";
