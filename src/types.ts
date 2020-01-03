export enum AlertType {
  Error = "error",
  Debug = "debug",
  Confirmation = "confirmation"
}

export type PerChartSelectionValue = {[index: string]: number[]};
export type SelectionValue = {[index: string]: PerChartSelectionValue};

export interface MidasElementFunctions {
  addCurrentSelectionMsg: (valueStr: string) => void;
  getCode: (dataFrame: string) => void;
  setUIItxFocus: (dataFrame?: string) => void;
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