
export { default as vegaEmbed } from "vega-embed";

import $ from "jquery";
import "jqueryui";

import "./elements.css";
import "./sidebar.css";

import { makeComm } from "./comm";
import MidasContainer from "./components/MidasContainer";
import { MidasSidebar } from "./components/MidasSidebar";
import { LogSteps } from "./utils";

import { SelectionShelf } from "./components/SelectionShelf";
import { ProfilerShelf } from "./components/ProfilerShelf";


declare global {
  interface Window {
    midas: MidasContainer;
    selectionShelf: SelectionShelf;
    profilerShelf: ProfilerShelf;
  }
}


export function load_ipython_extension() {

  Jupyter.notebook.events.on('kernel_connected.Kernel', function() {
    LogSteps("!!Kernel starting!!");
    
  });

  makeComm();
}