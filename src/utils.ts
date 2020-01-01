import { PerChartSelectionValue } from "./types";

export const STRICT = true;

export const FgRed = "\x1b[31m";
const FgGreen = "\x1b[32m";
const FgBlue = "\x1b[34m";
const FgMegenta = "\x1b[35m";
const FgGray = "\x1b[90m";
export const Reset = "\x1b[0m";

export function LogInternalError(message: string): null {
  console.log(`${FgRed}${message}${Reset}`);
  if (STRICT) {
    debugger;
    throw new Error(message);
  }
  return null;
}

export function comparePerChartSelection(s1: PerChartSelectionValue, s2: PerChartSelectionValue) {
  // iternate
  if (Object.keys(s1).length !== Object.keys(s2).length) {
    return false;
  }
  for (let k in Object.keys(s1)) {
    if (s1[k] !== s2[k]) {
      return false;
    }
  }
  return true;
}


export function executeCellId(cellId: string) {
  const idx = Jupyter.notebook.find_cell_index(cellId);
  if (idx < 0) throw LogInternalError(`Was not able to find cell ${cellId}`);
  Jupyter.notebook.select(idx);
  const cell = Jupyter.notebook.get_cell(idx);
  if (!cell) throw LogInternalError(`Was not able to find cell ${cellId}`);
  cell.code_mirror.display.lineDiv.scrollIntoView();
  cell.execute();
}

export function navigateToNotebookCell(cellId: string) {
  // note that this the the cell msg!
  LogDebug(`navigate to cell called for ${cellId}`);
  const cell = Jupyter.notebook.get_msg_cell(cellId);
  const index = Jupyter.notebook.find_cell_index(cell);
  if (!index) throw LogInternalError(`Was not able to find cell ${cellId}`);
  Jupyter.notebook.select(index);
  cell.code_mirror.display.lineDiv.scrollIntoView();
  // const cell_div = Jupyter.CodeCell.msg_cells[cellId];
  // if (cell_div) {
  //   cell_div
  // }
}

export function LogSteps(func: string, message?: string) {
  console.log(`${FgGreen}[${func}] ${message}${Reset}`);
}

export function LogDebug(message: string, obj?: any) {
  if (obj) {
    console.log(`${FgMegenta}${message}\n`, obj, `\n${Reset}`);
  } else {
    console.log(`${FgMegenta}${message}${Reset}`);
  }
}


export function getDigitsToRound(minVal: number, maxVal: number) {
  const diff = maxVal - minVal;
  const digits = Math.log(diff) / Math.log(10);
  if (digits < 1) {
    return Math.pow(10, Math.ceil(digits * -1) + 2);
  }
  return 1;
}

export function hashCode(str: string) {
  let hash = 0, i, chr;
  if (str.length === 0) return hash;
  for (i = 0; i < str.length; i++) {
    chr   = str.charCodeAt(i);
    hash  = ((hash << 5) - hash) + chr;
    hash |= 0; // Convert to 32bit integer
  }
  return hash;
}

export function getDfId(dfName: string) {
  return `df-${dfName}-chart`;
}

export function trimStr(s: string, len: number) {
  // assume that len is greater than 4
  // we are going to trim from the middle
  const amountToTrim = s.length - len;
  if (amountToTrim < 1) {
    return s;
  }
  const amountToKeep = Math.floor(len / 2) - 1;
  return s.slice(0, amountToKeep) + "..." + s.slice(s.length - amountToKeep, s.length);
}