import { LogDebug } from "./utils";

interface SingleCell {
  code: string;
  id: string;
  offset: number;
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

  makeSelection(selectionValue: string) {
    const idx = this.currentSelectionIgnoreList.findIndex(v => (v.selectionValue === selectionValue));
    if (idx > -1) {
      // ignore, also remove from ignore list
      delete this.currentSelectionIgnoreList[idx];
      LogDebug("Ignored!");
    } else {
      const date = new Date().toLocaleString("en-US");
      const text = `# [MIDAS] You selected the following from at time ${date}\n${this.midasInstanceName}.make_selections(${selectionValue})`;
      this.execute(text);
    }
  }

  executeFunction(funName: string, params: string) {
    const date = new Date().toLocaleString("en-US");
    const text = `# [MIDAS] ${date}\n${this.midasInstanceName}.${funName}(${params}})`;
    this.execute(text);
  }


  createCell(text: string) {
    const c = Jupyter.notebook.insert_cell_above("code");
    c.set_text(text);
    return c;
  }

  execute(text: string) {
    // we should see if we have just executed something exactly the same
    // if so, delete??
    // also if we have just executed a selection, and another came back, don't do anything
    const c = Jupyter.notebook.insert_cell_above("code");
    c.set_text(text);
    c.execute();
    return c.cell_id;
  }
}