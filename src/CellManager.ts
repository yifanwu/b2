import { LogDebug, commentUncommented, LogSteps, getEmojiEnnotatedComment, foldCode, showOrHideSelectionCells, findQueryCell, selectCell, deleteAllSelectionCells } from "./utils";
import { MIDAS_SELECTION_FUN, CELL_METADATA_FUN_TYPE, MIDAS_COLAPSE_CELL_CLASS, MIDAS_CURRENT_CLASS } from "./constants";
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
  reactiveCells: Map<string, Set<number>>;
  reactiveCellsReverse: Map<number, string>;
  showSelectionCells: boolean;

  constructor(midasInstanceName: string) {
    this.recordReactiveCell = this.recordReactiveCell.bind(this);
    this.toggleSelectionCells = this.toggleSelectionCells.bind(this);

    this.currentStep = 0;
    this.cellsCreated = [];
    this.midasInstanceName = midasInstanceName;
    this.prevFocus = undefined;
    this.currentFocus = undefined;
    this.lastExecutedCell = null;
    this.reactiveCells = new Map();
    this.reactiveCellsReverse = new Map();
    this.showSelectionCells = true;
  }

  setFocus(dfName?: string) {
    this.prevFocus = this.currentFocus;
    this.currentFocus = dfName;
  }

  /**
   * called by snapshot features.
   * @param div
   * @param comments
   */
  executeCapturedCells(div: string, comments: string) {
    this.createCell(`#${comments}\nfrom IPython.display import HTML, display\ndisplay(HTML("""${div}"""))`, "chart", true);
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

    function processCells(cells: Set<number>) {
      let cellIdxs: any[] = [];
      let newCells = new Set<number>();
      cells.forEach((c) => {
        const r = getCell(c);
        if (r) {
          cellIdxs.push(r);
          newCells.add(c);
        }
      });
      LogSteps(`[${dfName}] Reactively executing cells ${cellIdxs}`);
      Jupyter.notebook.execute_cells(cellIdxs);
      return newCells;
    }

    // processed separately to ensure that the splicing would work correctly
    const allCells = this.reactiveCells.get("");
    const dfCells = this.reactiveCells.get(dfName);
    if (allCells) {
      const newSet = processCells(allCells);
      // TODO: update the newSet
    }
    if (dfCells) processCells(dfCells);
  }


  recordReactiveCell(dfName: string, cellId: number) {
    if (!this.reactiveCells.has(dfName)) {
      this.reactiveCells.set(dfName, new Set());
    }
    this.reactiveCells.get(dfName).add(cellId);
    this.reactiveCellsReverse.set(cellId, dfName);
  }

  removeReactiveCell(cellId: number) {
    const dfName = this.reactiveCellsReverse.get(cellId);
    const cellSet = this.reactiveCells.get(dfName);
    cellSet.delete(cellId);
  }

  /**
   * This is triggered by the interactions
   * TODO: rename to indicate that this is used just by the interactions
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
      this.executeCell(cell, "interaction");
      // 1 because we want to leave the emoji
      // -1 because the last line is the line that executes
      foldCode(cell.code_mirror, 1, newCode.length - 1);
    } else {
      this.createCell(text, "interaction", true);
    }
    return;
  }

  getLastExecutedCellIdx() {
    if (this.lastExecutedCell) {
      return Jupyter.notebook.find_cell_index(this.lastExecutedCell);
    }
  }

  /**
   * note that we chose not to scroll for this
   *   because if we had competing scrolls (e.g., w/ a reactive cell), then the experinece may get confusing.
   * @param code
   * @param funKind
   */
  createCell(code: string, funKind: FunKind, shouldExecute: boolean) {
    // check if this has alredy been executed before
    if (funKind === "query") {
      const foundCell = findQueryCell(code);
      if (foundCell) {
        if (shouldExecute) {
          this.executeCell(foundCell, funKind);
        } else {
          // just scroll to it
          selectCell(foundCell, true);
        }
        return;
      }
    }
    // actually create if needed
    let cell;
    const idx = this.getLastExecutedCellIdx();
    if (idx) {
      cell = Jupyter.notebook.insert_cell_at_index("code", idx + 1);
    } else {
      LogDebug("Last executed cell not found!");
      const allCells = Jupyter.notebook.get_cells();
      const insertIdx = allCells.length;
      cell = Jupyter.notebook.insert_cell_at_index("code", insertIdx);
    }
    cell.metadata[CELL_METADATA_FUN_TYPE] = funKind;

    // modify content
    const comment = getEmojiEnnotatedComment(funKind);
    cell.set_text(comment + "\n" + code);
    // make sure that the notebook cell is selected
    // if we need to hide it
    if ((funKind === "interaction") && (!this.showSelectionCells)) {
      cell.element.addClass(MIDAS_COLAPSE_CELL_CLASS);
    }

    this.cellsCreated.push({
      code,
      funKind,
      cell,
      step: this.currentStep,
      time: new Date()
    });
    if (shouldExecute) {
      this.executeCell(cell, funKind);
    } else {
      selectCell(cell, false);
    }
    return cell;
  }

  toggleSelectionCells() {
    this.showSelectionCells = !this.showSelectionCells;
    showOrHideSelectionCells(this.showSelectionCells);
  }

  deleteAllSelectionCells() {
    if (confirm(`Are you sure you want to remove all selection cells so far? This cannot be undone.`)) {
      deleteAllSelectionCells();
    }
  }

  /**
   * we can use one of the following two:
   * - Jupyter.notebook.insert_cell_at_index(type, index);
   * - Jupyter.notebook.insert_cell_above("code");
   *
   * we are going to try with inserting at a fixed place
   */
  executeCell(cell: any, funKind: FunKind) {
    cell.execute();
    this.currentStep += 1;
    if (funKind === "query" || funKind === "chart") {
      selectCell(cell, true);
    }
    return cell.cell_id;
  }

  /**
   * To be called by the event listener to update CellManager
   * @param cell
   */
  updateLastExecutedCell(cell: any) {
    // remove prev
    if (this.lastExecutedCell) {
      this.lastExecutedCell.element.removeClass(MIDAS_CURRENT_CLASS);
    }
    this.lastExecutedCell = cell;
    // add new
    cell.element.addClass(MIDAS_CURRENT_CLASS);
  }
}