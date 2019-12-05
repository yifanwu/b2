import { LogDebug, navigateToNotebookCell } from "./utils";
import { MIDAS_SELECTION_FUN } from "./constants";

interface CellMetaData {
  funName: string;
  // without the comment
  params: string;
}

interface SingleCell {
  code: string;
  cell: any; // the only way to identify the cell is the entire object apparently?
  time: Date;
  metadata?: CellMetaData;
}

// TODO: we can also keep track of how the IDs have been moved around

export default class CellManager {
  cellsCreated: SingleCell[];
  currentSelectionIgnoreList: {selectionValue: string, timeCalled: Date}[];
  midasInstanceName: string;

  constructor(midasInstanceName: string) {
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
  }

  executeFunction(funName: string, params: string) {
    if (funName === MIDAS_SELECTION_FUN) {
      // check if it has been made before
      const idxBefore = this.cellsCreated.findIndex(v => (v.metadata) && (v.metadata.funName === MIDAS_SELECTION_FUN) && (v.metadata.params === params));
      if (idxBefore === (this.cellsCreated.length - 1) ) {
        LogDebug("Ignored becasue just executed");
        return; // no op
      }
      if (idxBefore > 0 ) {
        const cell = this.cellsCreated[idxBefore].cell;
        const cellIdx = Jupyter.notebook.find_cell_index(cell);
        Jupyter.notebook.select(cellIdx);
        cell.execute();
        LogDebug("executing from cells created earlier");
        return;
      }
    }
    const text = `${this.midasInstanceName}.${funName}(${params})`;
    this.execute(text, {funName, params });
    return;
  }

  execute(text: string, metadata?: CellMetaData) {
    const cell = Jupyter.notebook.insert_cell_above("code");
    const comment = `# [MIDAS] auto-created ${new Date().toLocaleString("en-US")}\n`;
    cell.set_text(comment + text);
    cell.code_mirror.display.lineDiv.scrollIntoView();
    cell.execute();
    this.cellsCreated.push({
      metadata,
      code: text,
      cell,
      time: new Date()
    });
    return cell.cell_id;
  }
}