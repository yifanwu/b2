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
  getCode: (dataFrame: string) => void;
  setUIItxFocus: (dataFrame?: string) => void;
  getChartCode: (dataFrame: string) => void;
  executeCapturedCells: (svg: string, comments: string) => void;
}

export interface MidasContainerFunctions {
  removeDataFrameMsg: (dataFrame: string) => void;
  elementFunctions: MidasElementFunctions;
}

export enum Context {
  SeenTogether = "SeenTogether",
  Derived = "Derived"
}

export enum DataType {
  Date = "Date",
}

// metric is the y axis (aggregation targets)
// trait is x axis (groupby targets)
export enum AnalysisType {
  Metric = "Metric",
  Trait = "Trait"
}

export enum ColumnType {
  Categorical = "Categorical",
  Linear = "Linear"
}