import { LogDebug, commentUncommented, LogInternalError, LogSteps } from "./utils";
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
  cell: any;
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
   *
   * current focus is set to the dataframe that currently has the focus
     if it is null, that means no one has the focus
     when new selections are made, they will replace the old one if the focus has NOT changed or switched to null.
      we need current and prev because otherwise
   */

  currentStep: number;
  cellsCreated: SingleCell[];
  midasInstanceName: string;
  prevFocus?: string;
  currentFocus?: string;
  lastExecutedCell?: any;
  reactiveCells: Map<string, number[]>;

  constructor(midasInstanceName: string) {
    this.captureCell = this.captureCell.bind(this);

    this.currentStep = 0;
    this.cellsCreated = [];
    this.midasInstanceName = midasInstanceName;
    this.prevFocus = undefined;
    this.currentFocus = undefined;
    this.lastExecutedCell = null;
    this.reactiveCells = new Map();
  }

  setFocus(dfName?: string) {
    this.prevFocus = this.currentFocus;
    this.currentFocus = dfName;
    // LogDebug(`Set focus: ${dfName}`);
  }

  executeCapturedCells(svg: string, comments: string) {
    this.createCellAndExecute(`#${comments}\nfrom IPython.display import SVG, display\ndisplay(SVG(data=\'${svg}\'))`, "chart");
  }

  runReactiveCells(dfName: string) {
    // "" is for all reactive cells
    function getCell(c: number) {
      const cIdxMsg = Jupyter.notebook.get_msg_cell(c);
      if (cIdxMsg) {
        const idx = Jupyter.notebook.find_cell_index(cIdxMsg);
        if (idx > -1) {
          LogDebug(`Found cell for ${dfName} with ${c}`);
          return idx;
        }
      }
      LogDebug(`One of the cells is no longer found for ${c}`);
    }

    function processCells(cells: number[]) {
      let cellIdxs = [];
      for (let i = 0; i < cells.length; i ++) {
        const r = getCell(cells[i]);
        if (r) {
          cellIdxs.push(r);
        } else {
          // remove if they are no longer available to save checking next time
          cells.splice(i, 1);
        }
      }
      LogSteps(`[${dfName}] Reactively executing cells ${cellIdxs}`);
      Jupyter.notebook.execute_cells(cellIdxs);
    }

    // processed separately to ensure that the splicing would work correctly
    const allCells = this.reactiveCells.get("");
    const dfCells = this.reactiveCells.get(dfName);
    if (allCells) processCells(allCells);
    if (dfCells) processCells(dfCells);
  }


  captureCell(dfName: string, cellId: number) {
    if (this.reactiveCells.has(dfName)) {
      this.reactiveCells.get(dfName).push(cellId);
    } else {
      this.reactiveCells.set(dfName, [cellId]);
    }
  }


  executeFunction(funName: string, params: string) {
    if (funName === MIDAS_SELECTION_FUN) {
      // check if the selection has been made before
      const idxBefore = this.cellsCreated.findIndex(v => (v.metadata) && (v.metadata.funName === MIDAS_SELECTION_FUN) && (v.metadata.params === params));

      if (idxBefore > -1) {
        if (this.cellsCreated[idxBefore].step === this.currentStep) {
          // LogDebug("Ignored becasue just executed");
          return;
        }
        const cell = this.cellsCreated[idxBefore].cell;
        const cellIdx = Jupyter.notebook.find_cell_index(cell);
        Jupyter.notebook.select(cellIdx);
        cell.execute();
        this.currentStep += 1;
        this.cellsCreated[idxBefore].step = this.currentStep;
        // LogDebug("executing from cells created earlier");
        return;
      }
    }
    const text = `${this.midasInstanceName}.${funName}(${params})`;
    // LogDebug(`Focus checking ${this.prevFocus}, ${this.currentFocus}`);
    if (this.prevFocus && this.currentFocus) {
      const cell = this.cellsCreated[this.cellsCreated.length - 1].cell;
      const old_code = cell.get_text();
      const commented = commentUncommented(old_code);
      // commnet out last uncommented
      this.exeucteCell(cell, `${commented}\n${text}`, "interaction");
    } else {
      this.createCellAndExecute(text, "interaction");
    }
    return;
  }

  createCellAndExecute(code: string, funKind: FunKind) {
    if (this.lastExecutedCell) {
      const idx = Jupyter.notebook.find_cell_index(this.lastExecutedCell);
      const cell = Jupyter.notebook.insert_cell_at_index("code", idx + 1);
      this.exeucteCell(cell, code, funKind);
    } else {
      const cell = Jupyter.notebook.insert_cell_below("code");
      this.exeucteCell(cell, code, funKind);
    }
  }
  /**
   * we can use one of the following two:
   * - Jupyter.notebook.insert_cell_at_index(type, index);
   * - Jupyter.notebook.insert_cell_above("code");
   *
   * we are going to try with inserting at a fixed place
   */
  exeucteCell(cell: any, text: string, funKind: FunKind, metadata?: CellMetaData) {
    const d = CELL_DOT_ANNOTATION[funKind];
    if (!d) LogInternalError(`FunKind ${funKind} was not found`);
    const time = new Date().toLocaleTimeString(navigator.language, {hour: "2-digit", minute: "2-digit"});
    const comment = `# ${d} ${time} ${d}\n`;
    cell.set_text(comment + text);
    cell.code_mirror.display.lineDiv.scrollIntoView();
    cell.execute();
    this.currentStep += 1;
    this.lastExecutedCell = cell;
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