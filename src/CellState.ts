import { LogDebug } from "./utils";

interface SingleCell {
  code: string;
  id: string;
  offset: number;
}

// TODO: we can also keep track of how the IDs have been moved around

export default class CellState {
  cellsCreated: SingleCell[];
  currentSelectionIgnoreList: {df: string, selectionValue: string, timeCalled: Date}[];
  constructor() {
    this.cellsCreated = [];
    this.currentSelectionIgnoreList = [];
  }

  addToIgnoreList(df: string, selectionValue: string) {
    const timeCalled = new Date();
    this.currentSelectionIgnoreList.push({
      df,
      selectionValue,
      timeCalled
    });
  }

  addSelectionToPython(dfName: string, selectionValue: string) {
    const idx = this.currentSelectionIgnoreList.findIndex(v => (v.df === dfName) && (v.selectionValue === selectionValue));
    if (idx > -1) {
      // ignore, also remove from ignore list
      delete this.currentSelectionIgnoreList[idx];
      LogDebug("Ignored!");
    } else {
      const date = new Date().toLocaleString("en-US");
      const text = `# [MIDAS] You selected the following from ${dfName} at time ${date}\nm.add_selection_by_interaction("${dfName}", ${selectionValue})`;
      this.execute(text);
    }
  }

  execute(text: string) {
    // we should see if we have just executed something exactly the same
    // if so, delete??
    // also if we have just executed a selection, and another came back, don't do anything
    LogDebug(`!!!!!!!!! execute ${text}`);
    const c = Jupyter.notebook.insert_cell_above("code");
    c.set_text(text);
    c.execute();
    return c.cell_id;
  }
}