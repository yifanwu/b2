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

export default class CellManager {

  /**
   * there is a mini state machine w.r.t how the brushes are fired on the boolean value of shouldDrawBrush
   * true ---> (itx) false
   * false ---> (drawBrush) true
   */

  currentStep: number;
  cellsCreated: SingleCell[];
  midasInstanceName: string;

  constructor(midasInstanceName: string) {
    this.currentStep = 0;
    this.cellsCreated = [];
    this.midasInstanceName = midasInstanceName;
  }


  makeSelection(selectionValue: string) {
    this.executeFunction(MIDAS_SELECTION_FUN, selectionValue);
  }

  executeFunction(funName: string, params: string) {
    if (funName === MIDAS_SELECTION_FUN) {
      // check if it has been made before
      const idxBefore = this.cellsCreated.findIndex(v => (v.metadata) && (v.metadata.funName === MIDAS_SELECTION_FUN) && (v.metadata.params === params));

      if (idxBefore > -1) {
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
      // we also need to add the brush
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