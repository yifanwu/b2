// CONFIG
export const IS_DEBUG = true;

// derived from config
export const EmbedConfig = IS_DEBUG
  ? {actions: true}
  : {actions: false}
  ;

// in px
export const CONTAINER_INIT_WIDTHS = 768; // set via css
export const PROFILTER_SHELF_WIDTH = 120; // set via css
export const MIN_SIDE_BAR_PX_WIDTH_FOR_DAHSBOARD_VIEW = 600;

// the following are configurations that affects how the UI behaves
export const DEBOUNCE_RATE = 100;
// export const ALERT_ALIVE_TIME = 100000;
export const SHELF_TEXT_MAX_LEN = 14;
export const SELECTION_TEXT_MAX_LEN = 13;

// The rest of this file is synchronized with the Python scripts
// need to keep this in sync with the defaults.py file
// TODO:  maybe consider changing this to a JSON file for better synchronization
export const MIDAS_CELL_COMM_NAME = "midas-cell-comm";
export const MIDAS_RECOVERY_COMM_NAME = "midas-recovery-comm";
export const MIDAS_SELECTION_FUN = "sel";

// some weird name because we are using vega-lite generated code
export const DEFAULT_DATA_SOURCE = "source_0";
export const COUNT_COL_NAME = "count";
export const IS_OVERVIEW_FIELD_NAME = "is_overview";

export const BRUSH_SIGNAL = "brush";
export const BRUSH_X_SIGNAL = "brush_x";
export const BRUSH_Y_SIGNAL = "brush_y";
// the following is used when the brush is on a single item
export const MIN_BRUSH_PX = 5;

export const MULTICLICK_SIGNAL = "select";
export const MULTICLICK_PIXEL_SIGNAL = "select_tuple";
export const MULTICLICK_TOGGLE = "select_toggle";

// some div ids that we use
export const SNAPSHOT_BUTTON = "midas-snap-shot-all";
export const TOGGLE_PANNEL_BUTTON = "midas-toggle-pannel";
export const TOGGLE_MIDAS_BUTTON = "midas-toggle-all";