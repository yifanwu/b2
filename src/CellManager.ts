import { LogDebug, commentUncommented, LogSteps, getEmojiEnnotatedComment, foldCode } from "./utils";
import { MIDAS_SELECTION_FUN } from "./constants";
import { FunKind } from "./types";


// interface CellMetaData {
//   funName: string;
//   // without the comment
//   params: string;
// }

interface SingleCell {
  code: string;
  cell: any;
  time: Date;
  step: number;
  funKind: FunKind;
  // metadata?: CellMetaData;
}

// interface ReactiveCell {
//   cellPos: number;
//   appendFlag: boolean;
// }

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
    this.recordReactiveCell = this.recordReactiveCell.bind(this);

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

  executeCapturedCells(div: string, comments: string) {
    const cell = this.createCell(`#${comments}\nfrom IPython.display import HTML, display\ndisplay(HTML("""${div}"""))`, "chart", true);
    cell.code_mirror.display.lineDiv.scrollIntoView();
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


  recordReactiveCell(dfName: string, cellId: number) {
    if (this.reactiveCells.has(dfName)) {
      this.reactiveCells.get(dfName).push(cellId);
    } else {
      this.reactiveCells.set(dfName, [cellId]);
    }
  }


  /**
   * This is triggered by the interactions
   * @param funName
   * @param params
   */
  executeFunction(funName: string, params: string) {
    const text = `${this.midasInstanceName}.${funName}(${params})`;
    if ((funName === MIDAS_SELECTION_FUN) && this.prevFocus && this.currentFocus) {
      const cell = this.cellsCreated[this.cellsCreated.length - 1].cell;
      const oldCode = cell.get_text();

      const emojiComment = getEmojiEnnotatedComment("interaction");
      const newCode = commentUncommented(oldCode, text);
      // now make sure the code is foled!
      const newText = emojiComment + "\n" + newCode.join("\n");
      cell.set_text(newText);
      this.exeucteCell(cell);
      // 1 because we want to leave the emoji
      // -1 because the last line is the line that executes
      foldCode(cell.code_mirror, 1, newCode.length - 1);
    } else {
      this.createCell(text, "interaction", true);
    }
    return;
  }

  /**
   * this is invoked by none-selections code effects
   * @param code
   * @param funKind
   */
  createCell(code: string, funKind: FunKind, shouldExecute: boolean) {
    let cell;
    if (this.lastExecutedCell) {
      const idx = Jupyter.notebook.find_cell_index(this.lastExecutedCell);
      cell = Jupyter.notebook.insert_cell_at_index("code", idx + 1);
    } else {
      LogDebug("Last executed cell not found!");
      cell = Jupyter.notebook.insert_cell_below("code");
    }
    const comment = getEmojiEnnotatedComment(funKind);
    cell.set_text(comment + "\n" + code);
    // make sure that the notebook cell is selected
    const currentIdx = Jupyter.notebook.find_cell_index(cell);
    Jupyter.notebook.select(currentIdx);
    // cell.code_mirror.display.lineDiv.scrollIntoView();
    this.cellsCreated.push({
      code,
      funKind,
      cell,
      step: this.currentStep,
      time: new Date()
    });
    if (shouldExecute) {
      this.exeucteCell(cell);
    }
    return cell;
  }

  /**
   * we can use one of the following two:
   * - Jupyter.notebook.insert_cell_at_index(type, index);
   * - Jupyter.notebook.insert_cell_above("code");
   *
   * we are going to try with inserting at a fixed place
   */
  exeucteCell(cell: any) {
    cell.execute();
    this.currentStep += 1;
    this.lastExecutedCell = cell;
    return cell.cell_id;
  }
}