import { PerChartSelectionValue, SelectionValue } from "./types";

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



function compareArray(as: SelectionValue, bs: SelectionValue) {
  // REDZONE --- this part has been buggy historically...
  if (as.length !== bs.length) return false;
  // @ts-ignore, union typing string and number is causing some issues here.
  for (let a of as) if (bs.indexOf(a) < 0) return false;
  return true;
}


/**
 * @param s1 one selection
 * @param s2 another selections
 * returns false if the two values are not the same, and true if the same
 */
export function comparePerChartSelection(s1?: PerChartSelectionValue, s2?: PerChartSelectionValue) {
  if (s1 && s2) {
    // iternate
    if (Object.keys(s1).length !== Object.keys(s2).length) {
      return false;
    }
    for (let k of Object.keys(s1)) {
      // this doesn't work because we need to compare array values
      if (!compareArray(s1[k], s2[k])) {
        return false;
      }
    }
    return true;
  } else if (s1) {
    return false;
  } else if (s2) {
    return false;
  } else {
    // both must be null
    return true;
  }
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

export function commentUncommented(code: string) {
  const newCode: string[] = [];
  for (let l of code.split("\n")) {
    LogDebug("code", l);
    if (l.length > 0) {
      // check if starts with "#"
      if (!l.includes("🔵")) {
        if (l[0] !== "#") {
          LogDebug("adding with #", l);
          newCode.push(`# ${l}`);
        } else {
          LogDebug("adding", l);
          newCode.push(l);
        }
      }
    }
  }
  return newCode.join("\n");
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