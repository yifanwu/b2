/**
 * All the following code is taken from
 *
 * https://github.com/ipython-contrib/jupyter_contrib_nbextensions/blob/master/src/jupyter_contrib_nbextensions/nbextensions/codefolding/
 */

import { INTERACT_EMOJI } from "./constants";

function restoreFolding(cell: any, codecell: any) {
  if (cell.metadata.code_folding === undefined || !(cell instanceof codecell.CodeCell)) {
    return;
  }
  // visit in reverse order, as otherwise nested folds un-fold outer ones
  let lines = cell.metadata.code_folding.slice().sort();
  for (let idx = lines.length - 1; idx >= 0; idx--) {
    let line = lines[idx];
    let opts = cell.code_mirror.state.foldGutter.options;
    let linetext = cell.code_mirror.getLine(line);
    if (linetext !== undefined) {
      cell.code_mirror.foldCode(CodeMirror.Pos(line, 0), opts.rangeFinder);
    }
    else {
      // the line doesn't exist, so we should remove it from metadata
      cell.metadata.code_folding = lines.slice(0, idx);
    }
    cell.code_mirror.refresh();
  }
}

function activate_cm_folding (cm: any) {
  let gutters = cm.getOption("gutters").slice();
  if ($.inArray("CodeMirror-foldgutter", gutters) < 0) {
    gutters.push("CodeMirror-foldgutter");
    cm.setOption("gutters", gutters);
  }

  /* set indent or brace folding */
  let opts: any = true;
  if (Jupyter.notebook) {
    opts = {
      rangeFinder: new CodeMirror.fold.combine(
        CodeMirror.fold.firstline,
        CodeMirror.fold.magic,
        CodeMirror.fold.blockcomment,
        cm.getMode().fold === "indent" ? CodeMirror.fold.indent : CodeMirror.fold.brace
      )
    };
  }
  cm.setOption("foldGutter", opts);
}

function updateMetadata (cm: any) {
  let list = cm.getAllMarks();
  let lines = [];
  for (let i = 0; i < list.length; i++) {
    if (list[i].__isFold) {
      let range = list[i].find();
      lines.push(range.from.line);
    }
  }
  /* User can click on gutter of unselected cells, so make sure we store metadata in the correct cell */
  let cell = Jupyter.notebook.get_selected_cell();
  if (cell.code_mirror !== cm) {
    let cells = Jupyter.notebook.get_cells();
    let ncells = Jupyter.notebook.ncells();
    for (let k = 0; k < ncells; k++) {
      let _cell = cells[k];
      if (_cell.code_mirror === cm ) { cell = _cell; break; }
    }
  }
  cell.metadata.code_folding = lines;
}

function regFoldHelper() {
  CodeMirror.registerHelper("fold", "firstline", function(cm: any, start: any) {
    let mode = cm.getMode(), Token = mode.lineComment;
    if (start.line === 0) {
      let lineText = cm.getLine(start.line);
      let found = lineText.lastIndexOf(Token, 0);
      if (found === 0) {
        // the following is customization for midas
        // if there is a blue emoji then do not comment the last line out
        // ideally we can access the metadata, but hack works for now
        const end = lineText.includes(INTERACT_EMOJI)
          ? cm.lastLine() - 1
          : cm.lastLine()
          ;
        return {
          from: CodeMirror.Pos(start.line, null),
          to: CodeMirror.Pos(end, null)
        };
      }
    }
    return null;
  });
}

function regMagicHelper() {
  CodeMirror.registerHelper("fold", "magic", function(cm: any, start: any) {
    let mode = cm.getMode(), Token = "%%";
    if (start.line === 0) {
      let lineText = cm.getLine(start.line);
      let found = lineText.lastIndexOf(Token, 0);
      if (found === 0) {
      const end =  cm.lastLine();
      return {
        from: CodeMirror.Pos(start.line, null),
        to: CodeMirror.Pos(end, null)
      };
      }
    }
    return null;
  });
}

function regBlockHelper() {
  CodeMirror.registerHelper("fold", "blockcomment", function(cm: any, start: any) {
    let mode = cm.getMode(), Token = mode.lineComment;
    let lineText = cm.getLine(start.line);
    let found = lineText.lastIndexOf(Token, 0);
    if (found === 0) {  // current line is a comment
      if (start.line === 0) {
        found = -1;
      } else {
        lineText = cm.getLine(start.line - 1);
        found = lineText.lastIndexOf(Token, 0);
      }
      if (start.line === 0 || found !== 0) {  // no previous comment line
        let end = start.line;
        for (let i = start.line + 1; i <= cm.lastLine(); ++i) {  // final comment line
          lineText = cm.getLine(i);
          found = lineText.lastIndexOf(Token, 0);
          if (found === 0) {
            end = i;
          } else {
            break;
          }
        }
        if (end > start.line) {
        return {from: CodeMirror.Pos(start.line, null),
            to: CodeMirror.Pos(end, null)};
        }
      }
    }
    return null;
  });
}

function toggleFolding () {
  let cm;
  let pos = {line: 0, ch: 0, xRel: 0};
  if (Jupyter.notebook !== undefined) {
    cm = Jupyter.notebook.get_selected_cell().code_mirror;
    if (Jupyter.notebook.mode === "edit") {
      pos = cm.getCursor();
    }
  }
  else {
    cm = Jupyter.editor.codemirror;
    pos = cm.getCursor();
  }
  let opts = cm.state.foldGutter.options;
  cm.foldCode(pos, opts.rangeFinder);
}



export function setUpCodeFolding(codecell: any, requirejs: any, configmod: any) {

  // putting here for scoping
  function initExistingCells() {
    let cells = Jupyter.notebook.get_cells();
    let ncells = Jupyter.notebook.ncells();
    for (let i = 0; i < ncells; i++) {
      let cell = cells[i];
      if ((cell instanceof codecell.CodeCell)) {
      activate_cm_folding(cell.code_mirror);
      /* restore folding state if previously saved */
      restoreFolding(cell, codecell);
      cell.code_mirror.on("fold", updateMetadata);
      cell.code_mirror.on("unfold", updateMetadata);
      }
    }

    // REDZONE: if anything else listens to create.Cell, gotta watch out
    Jupyter.notebook.events.unbind("create.Cell");
    Jupyter.notebook.events.on("create.Cell", createCell);
  }

  function createCell(_: any, nbcell: any) {
    const cell = nbcell.cell;
    if ((cell instanceof codecell.CodeCell)) {
      activate_cm_folding(cell.code_mirror);
      cell.code_mirror.on("fold", updateMetadata);
      cell.code_mirror.on("unfold", updateMetadata);
      // queue restoring folding, to run once metadata is set, hopefully.
      // This can be useful if cells are un-deleted, for example.
      setTimeout(function () { restoreFolding(cell, codecell); }, 500);
    }
  }

  function on_config_loaded () {
    if (Jupyter.notebook !== undefined) {
      // register actions with ActionHandler instance
      let prefix = "auto";
      let name = "toggle-codefolding";
      let action = {
      icon: "fa-comment-o",
      help    : "Toggle codefolding",
      help_index : "ec",
      id : "toggle_codefolding",
      handler : toggleFolding
      };
      let action_full_name = Jupyter.keyboard_manager.actions.register(action, name, prefix);

      // define keyboard shortcuts
      let edit_mode_shortcuts = {};
      edit_mode_shortcuts[params.codefolding_hotkey] = action_full_name;

      // register keyboard shortcuts with keyboard_manager
      Jupyter.notebook.keyboard_manager.edit_shortcuts.add_shortcuts(edit_mode_shortcuts);
      Jupyter.notebook.keyboard_manager.command_shortcuts.add_shortcuts(edit_mode_shortcuts);
    }
    else {
      // we're in edit view
      let extraKeys = Jupyter.editor.codemirror.getOption("extraKeys");
      extraKeys[params.codefolding_hotkey] = toggleFolding;
      CodeMirror.normalizeKeyMap(extraKeys);
      console.log("[codefolding] binding hotkey", params.codefolding_hotkey);
      Jupyter.editor.codemirror.setOption("extraKeys", extraKeys);
    }
  }

  let params = {
    codefolding_hotkey : "Alt-f",
    init_delay : 1000
  };

  // updates default params with any specified in the provided config data
  let update_params = function (config_data: any) {
    for (let key in params) {
      if (config_data.hasOwnProperty(key)) {
        params[key] = config_data[key];
      }
    }
  };

  let conf_sect: any;
  if (Jupyter.notebook) {
    // we're in notebook view
    conf_sect = Jupyter.notebook.config;
  }
  else if (Jupyter.editor) {
    // we're in file-editor view
    conf_sect = new configmod.ConfigSection("notebook", {base_url: Jupyter.editor.base_url});
    conf_sect.load();
  }
  else {
    // we're some other view like dashboard, terminal, etc, so bail now
    return;
  }

  conf_sect.loaded
  .then(function () { update_params(conf_sect.data); })
  .then(on_config_loaded);

  if (Jupyter.notebook) {
    regFoldHelper();
    regMagicHelper();
    regBlockHelper();
    /* require our additional custom codefolding modes before initialising fully */
    if (Jupyter.notebook._fully_loaded) {
    setTimeout(function () {
      console.log("Codefolding: Wait for", params.init_delay, "ms");
      initExistingCells();
    }, params.init_delay);
    }
    else {
    Jupyter.notebook.events.one("notebook_loaded.Notebook", initExistingCells);
    }
  }
  else {
    activate_cm_folding(Jupyter.editor.codemirror);
    setTimeout(function () {
    console.log("Codefolding: Wait for", params.init_delay, "ms");
    Jupyter.editor.codemirror.refresh();
    }, params.init_delay);
  }
}