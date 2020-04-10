import { PerChartSelectionValue, SelectionValue, FunKind, MidasContainerFunctions } from "./types";
import { SelectionDimensions } from "./charts/vegaGen";
import { CELL_METADATA_FUN_TYPE, MIDAS_COLAPSE_CELL_CLASS, IS_DEBUG, TOGGLE_SELECTION_BUTTON, MIDAS_CONTAINER_ID, MIDAS_BUSY_CLASS, INTERACT_EMOJI, BUTTON_GROUP_ID } from "./constants";
import CellManager from "./CellManager";
import { LoggerFunction, LogCode, LogDataframeInteraction } from "./logging";

export const STRICT = true;

export const FgRed = "\x1b[31m";
const FgGreen = "\x1b[32m";
const FgBlue = "\x1b[34m";
const FgMegenta = "\x1b[35m";
const FgGray = "\x1b[90m";
export const Reset = "\x1b[0m";

const CELL_EMOJI_ANNOTATION = {
  "chart": "🟠",
  "query": "🟡",
  "interaction": INTERACT_EMOJI,
};


export function throttle(fn: any, wait: number) {
  let time = Date.now();
  return function() {
    if ((time + wait - Date.now()) < 0) {
      fn();
      time = Date.now();
    }
  };
}


/**
 * set up the Jupyter event listeners
 */
export function setupJupyterEvents(cellManager: CellManager, logger: LoggerFunction) {
  // unbind is important
  // - otherwise if midas is loaded again, both are registered
  // - ok to remove all because there is no internal Jupyter consumers of this particular event
  //   verified by a global grep on the repo, might not work nice with other extensions though
  Jupyter.notebook.events.unbind("finished_execute.CodeCell");
  Jupyter.notebook.events.on("finished_execute.CodeCell", function(_: any, data: any) {
    // we also need to tell cell manager which one was the most recently ran!
    cellManager.updateLastExecutedCell(data.cell);

    // passed to Python for more logging
    const rawCode = data.cell.get_text();
    let trimmedString = rawCode;
    if (rawCode.includes("display(HTML(")) {
      trimmedString = rawCode.replace(/display\(HTML\(.*\)\)/, "display(HTML(...))");
    }
    const entry: LogCode = {
      action: "coding",
      code: trimmedString,
      actionKind: "code",
      cellId: data.cell.cell_id,
      cellPos: Jupyter.notebook.find_cell_index(data.cell),
    };
    logger(entry);
  });
  // also need to instrument markdowncells
  // using "rendered.MarkdownCell" because
  // - I cannot find the creation event
  // - rendered might be a better proxy since they might change the values
  // the only issue is if the people forget to render it, oh well : /
  Jupyter.notebook.events.unbind("rendered.MarkdownCell");
  Jupyter.notebook.events.on("rendered.MarkdownCell", function(_: any, data: any) {
    cellManager.updateLastExecutedCell(data.cell);
    const code = data.cell.get_text();
    const entry: LogCode = {
      action: "markdown_rendered",
      code,
      actionKind: "text",
      cellId: data.cell.cell_id,
      cellPos: Jupyter.notebook.find_cell_index(data.cell),
    };
    logger(entry);
  });
}

export function enableMidasInteractions() {
  const container = document.getElementById(MIDAS_CONTAINER_ID);
    if (container) {
      // also set the global flag
      (window as any).midasSelectionEnabled = true;
      container.classList.remove(MIDAS_BUSY_CLASS);
    }
}

export function disableMidasInteractions() {
  const container = document.getElementById(MIDAS_CONTAINER_ID);
  if (container) {
    (window as any).midasSelectionEnabled = false;
    container.classList.add(MIDAS_BUSY_CLASS);
  }
}

export function getContainerFunctions(
  comm: any,
  logger: LoggerFunction,
  setUIItxFocus: (dfName?: string) => void,
  executeCapturedCells: (div: string, comments: string) => void) {

  const removeDataFrameMsg = (dfName: string) => {
    comm.send({
      "command": "remove-dataframe",
      "df_name": dfName,
    });
    const entry: LogDataframeInteraction = {
      action: "remove_df",
      actionKind: "uiControl",
      dfName,
    };
    logger(entry);
  };

  const addCurrentSelectionMsg = (valueStr: string) => {
    comm.send({
      "command": "add_current_selection",
      "value": valueStr
    });
  };

  const getChartCode = (dfName: string) => {
    comm.send({
      "command": "get-visualization-code-clipboard",
      "df_name": dfName
    });
  };

  const containerFunctions: MidasContainerFunctions = {
    removeDataFrameMsg,
    elementFunctions: {
      logger,
      addCurrentSelectionMsg,
      setUIItxFocus,
      getChartCode,
      executeCapturedCells
    }
  };
  return containerFunctions;
}


export function setupCellManagerUIChanges(cellManager: CellManager) {
  addNotebookMenuBtn(
    cellManager.toggleSelectionCells,
    TOGGLE_SELECTION_BUTTON,
    `Toggle ${INTERACT_EMOJI}`,
    "Click to toggle Midas selection cells.",
  );
  // addNotebookMenuBtn(
  //   cellManager.deleteAllSelectionCells,
  //   DELETE_SELECTION_BUTTON,
  //   `✂️ all selection cells`,
  //   "Click to delete all selection cells so far."
  // );
}

export function LogInternalError(message: string): null {
  console.log(`${FgRed}${message}${Reset}`);
  if (STRICT) {
    debugger;
    throw new Error(message);
  }
  return null;
}

export function createMenuBtnGroup() {
  if ($(`#${BUTTON_GROUP_ID}`).length > 0) {
    return;
  }
  const newButtonGroup = `<div class="btn-group" id="${BUTTON_GROUP_ID}"></div>`;
  $("#maintoolbar-container").append(newButtonGroup);
}

export function addNotebookMenuBtn(onClick: () => void, btnId: string, btnText: string, btnTitle: string) {

  // create if does not exist
  const newButton = `<button
      id="${btnId}"
      class="btn btn-default one-time-animation"
      title=${btnTitle}
    >${btnText}</button>`;

  if ($(`#${btnId}`).length > 0) {
    $(`#${btnId}`).off("click");
    // $(`#${btnId}`).replaceWith(newButton);
  } else {
    $(`#${BUTTON_GROUP_ID}`).append(newButton);
  }
  $(`#${btnId}`).click(() => onClick());
}

export function getEmojiEnnotatedComment(funKind: FunKind) {
  const d = CELL_EMOJI_ANNOTATION[funKind];
  if (!d) LogInternalError(`FunKind ${funKind} was not found`);
  const time = new Date().toLocaleTimeString(navigator.language, {hour: "2-digit", minute: "2-digit"});
  const comment = `# ${d} ${time} ${d}`;
  return comment;
}

/**
 * Returns true if the two arrays have the same values
 *         false if different
 * @param as first array of selection values
 * @param bs second array of selection values
 */
function compareArray(as: SelectionValue, bs: SelectionValue) {
  // REDZONE --- this part has been buggy historically...
  if (as.length !== bs.length) return false;

  for (let a of as) {
    // @ts-ignore, union typing string and number is causing some issues here.
    if (bs.indexOf(a) < 0) {
      return false;
    }
  }
  return true;
}

export function copyTextToClipboard(text: string) {
  const textArea = document.createElement("textarea");

  // Place in top-left corner of screen regardless of scroll position.
  textArea.style.position = "fixed";
  textArea.style.top = "0";
  textArea.style.left = "0";

  // Ensure it has a small width and height. Setting to 1px / 1em
  // doesn't work as this gives a negative w/h on some browsers.
  textArea.style.width = "2em";
  textArea.style.height = "2em";

  // We don't need padding, reducing the size if it does flash render.
  textArea.style.padding = "0";

  // Clean up any borders.
  textArea.style.border = "none";
  textArea.style.outline = "none";
  textArea.style.boxShadow = "none";

  // Avoid flash of white box if rendered for any reason.
  textArea.style.background = "transparent";

  textArea.value = text;

  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();

  try {
    let successful = document.execCommand("copy");
    let msg = successful ? "successful" : "unsuccessful";
    console.log("Copying text command was " + msg);
  } catch (err) {
    console.log("Oops, unable to copy");
  }

  document.body.removeChild(textArea);
}


/**
 * this is the case when the second selection has more charts specified
 * returns false if the two values are not the same, and true if the same
 * @param s1 one selection
 * @param s2 another selections
 */
export function isFirstSelectionContainedBySecond(s1?: PerChartSelectionValue, s2?: PerChartSelectionValue) {
  if (s1 && Object.keys(s1).length && s2 && Object.keys(s2).length) {
    // iternate
    if (Object.keys(s1).length > Object.keys(s2).length) {
      return false;
    }
    for (let k of Object.keys(s1)) {
      // this doesn't work because we need to compare array values
      if (!compareArray(s1[k], s2[k])) {
        return false;
      }
    }
    return true;
  } else if (s1 && Object.keys(s1).length) {
    return false;
  } else if (s2 && Object.keys(s2).length) {
    return false;
  } else {
    // both must be null
    return true;
  }
}


export function selectCell(cell: any, scroll: boolean) {
  const currentIdx = Jupyter.notebook.find_cell_index(cell);
  if (!currentIdx) {
    LogInternalError(`Was not able to find cel`);
  } else {
    Jupyter.notebook.select(currentIdx);
    if (scroll) {
      cell.code_mirror.display.lineDiv.scrollIntoView({behavior: "smooth"});
    }
  }
}


export function navigateToNotebookCell(cellId: string) {
  // note that this the the cell msg!
  LogDebug(`navigate to cell called for ${cellId}`);
  const cell = Jupyter.notebook.get_msg_cell(cellId);
  selectCell(cell, true);
}

/**
 * @param cm code_mirror field of the notebook cell
 * @param from line number to fold from
 * @param to line number to fold to
 */
export function foldCode(cm: any, from: number, to: number) {
  // const cm = Jupyter.notebook.get_selected_cell().code_mirror;
  const unFoldRangeFinder = (a: any, b: any) => {return {from: CodeMirror.Pos(from, 0), to: CodeMirror.Pos(from, 0)}; };
  cm.foldCode(CodeMirror.Pos(from, 0), unFoldRangeFinder, "unfold");
  const rangeFinder = (a: any, b: any) => {return {from: CodeMirror.Pos(from, 0), to: CodeMirror.Pos(to, 0)}; };
  cm.foldCode(CodeMirror.Pos(from, 0), rangeFinder, "fold");
}

function getUncommentedCode(code: string) {
  let all = [];
  for (let l of code.split("\n")) {
    if (l[0] !== "#") {
      all.push(l);
    }
  }
  return all;
}

function commentIfNot(l: string) {
  if (l[0] !== "#") {
    return `# ${l}`;
  }
  return l;
}

/**
 * 
 * @param code
 * @param newLine
 */
export function commentUncommented(code: string, newLine: string) {
  const newCode: string[] = [];
  for (let l of code.split("\n")) {
    if (!((l.length === 0) || l.includes("🔵") || l.includes(newLine))) {
      newCode.push(commentIfNot(l));
    }
    //  else {
    //   debugger;
    // }
  }
  newCode.push(newLine);
  return newCode;
}

export function LogSteps(func: string, message?: string) {
  console.log(`${FgGreen}[${func}] ${message}${Reset}`);
}

export function LogDebug(message: string, obj?: any) {
  // don't print if we are in release
  if (!IS_DEBUG) return;
  if (obj) {
    console.log(`${FgMegenta}${message}\n`, obj, `\n${Reset}`);
  } else {
    console.log(`${FgMegenta}${message}${Reset}`);
  }
}

export function deleteAllSelectionCells() {
  const cells = getCellsByFunKind("interaction");
  for (let c of cells) {
    const idx = Jupyter.notebook.find_cell_index(c);
    Jupyter.notebook.delete_cells([idx]);
  }
}

export function showOrHideSelectionCells(show: boolean) {
  const cells = getCellsByFunKind("interaction");
  // based on code like this
  // https://github.com/jupyter/notebook/blob/70d74d21ac051fbeaa81d4ef4fff9fa759de96d7/notebook/static/notebook/js/cell.js#L165
  cells.map((c: any) => {
    if (show) {
      c.element.removeClass(MIDAS_COLAPSE_CELL_CLASS);
    } else {
      c.element.addClass(MIDAS_COLAPSE_CELL_CLASS);
    }
  });
}

function getCellsByFunKind(funKind: FunKind) {
  const allCells = Jupyter.notebook.get_cells();
  const selectionCells = allCells.filter((c: any) => (CELL_METADATA_FUN_TYPE in c.metadata) && c.metadata[CELL_METADATA_FUN_TYPE] === funKind);
  return selectionCells;
}


/**
 * Note that this function has HEAVY hard coding
 * @param code
 */
export function findQueryCell(code: string) {
  // strip all comments and see if it's the same
  const uncommented = getUncommentedCode(code);
  if (uncommented.length === 0) {
    return LogInternalError("chart should have at least one line");
  }
  const cells = getCellsByFunKind("query");
  for (let c of cells) {
    const text = getUncommentedCode(c.get_text());
    if (uncommented.join("\n") === text.join("\n")) {
      return c;
    }
  }
  return null;
}

export function getDigitsToRound(minVal: number, maxVal: number) {
  // asset order
  if (minVal > maxVal) {
    LogInternalError(`getDigitsToRound must receive ordered arguments, but we got ${minVal}, ${maxVal}`);
  }
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

export function getChartDetailId(dfName: string) {
  return `df-${dfName}-controls`;
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

// very vega specific
// note that we can only support one valyue at a time otherwis3e vega is going to error out
export function getMultiClickValue(selName: string, value: string|number, selChannel: SelectionDimensions) {
  return {"unit": "", "fields": [{"field": selName, "channel": selChannel, "type": "E"}], "values": [value]};
}
