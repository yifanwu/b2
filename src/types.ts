export enum AlertType {
  Error = "error",
  Debug = "debug",
  Confirmation = "confirmation"
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