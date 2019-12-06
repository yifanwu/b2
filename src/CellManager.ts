import { LogDebug, navigateToNotebookCell, LogInternalError } from "./utils";
import { MIDAS_SELECTION_FUN } from "./constants";

const CELL_DOT_ANNOTATION = {
  "chart": "🟠",
  "query": "🟡",
  "interaction": "🔵",
};

export type FunKind = "chart" | "query" | "interaction";

interface CellMetaData {
  funName: string;
  // without the comment
  params: string;
}

interface SingleCell {
  code: string;
  cell: any; // the only way to identify the cell is the entire object apparently?
  time: Date;
  step: number;
  funKind: FunKind;
  metadata?: CellMetaData;
}

// TODO: we can also keep track of how the IDs have been moved around

export default class CellManager {
  currentStep: number;
  cellsCreated: SingleCell[];
  currentSelectionIgnoreList: {selectionValue: string, timeCalled: Date}[];
  midasInstanceName: string;

  constructor(midasInstanceName: string) {
    this.currentStep = 0;
    this.cellsCreated = [];
    this.currentSelectionIgnoreList = [];
    this.midasInstanceName = midasInstanceName;
  }

  addToIgnoreList(selectionValue: string) {
    const timeCalled = new Date();
    this.currentSelectionIgnoreList.push({
      selectionValue,
      timeCalled
    });
  }

  makeSelectionFromCharts(selectionValue: string) {
    // note that this is called from the JS side (Vega)!
    const idx = this.currentSelectionIgnoreList.findIndex(v => (v.selectionValue === selectionValue));
    if (idx > -1) {
      // ignore, also remove from ignore list
      delete this.currentSelectionIgnoreList[idx];
      LogDebug("Ignored due to python triggered brushing!");
      return;
    }
    // otherwise
    this.executeFunction(MIDAS_SELECTION_FUN, selectionValue);
  }

  executeFunction(funName: string, params: string) {
    if (funName === MIDAS_SELECTION_FUN) {
      // check if it has been made before
      const idxBefore = this.cellsCreated.findIndex(v => (v.metadata) && (v.metadata.funName === MIDAS_SELECTION_FUN) && (v.metadata.params === params));

      if (idxBefore > 0) {
        if (this.cellsCreated[idxBefore].step === this.currentStep) {
          LogDebug("Ignored becasue just executed");
          return; // no op
        }
        const cell = this.cellsCreated[idxBefore].cell;
        const cellIdx = Jupyter.notebook.find_cell_index(cell);
        Jupyter.notebook.select(cellIdx);
        cell.execute();
        this.currentStep += 1;
        this.cellsCreated[idxBefore].step = this.currentStep;
        LogDebug("executing from cells created earlier");
        return;
      }
    }
    const text = `${this.midasInstanceName}.${funName}(${params})`;
    this.create_cell_and_execute(text, "interaction", {funName, params });
    return;
  }

  create_cell_and_execute(text: string, funKind: FunKind, metadata?: CellMetaData) {
    const cell = Jupyter.notebook.insert_cell_above("code");
    const d = CELL_DOT_ANNOTATION[funKind];
    if (!d) LogInternalError(`FunKind ${funKind} was not found`);
    const time = new Date().toLocaleTimeString(navigator.language, {hour: "2-digit", minute: "2-digit"});
    const comment = `# ${d} ${time} ${d}\n`;
    cell.set_text(comment + text);
    cell.code_mirror.display.lineDiv.scrollIntoView();
    cell.execute();
    this.currentStep += 1;
    this.cellsCreated.push({
      metadata,
      code: text,
      funKind,
      cell,
      step: this.currentStep,
      time: new Date()
    });
    return cell.cell_id;
  }
}