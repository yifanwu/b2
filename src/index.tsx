
export { default as vegaEmbed } from "vega-embed";

import $ from "jquery";
import "jqueryui";

import "./elements.css";

import { makeComm, openRecoveryComm } from "./comm";
import MidasContainer from "./components/MidasContainer";
import { MidasSidebar } from "./components/MidasSidebar";
import { LogSteps } from "./utils";

import { SelectionShelf } from "./components/SelectionShelf";
import { ProfilerShelf } from "./components/ProfilerShelf";
import {tearDownMidasComponent} from "./setup"

declare global {
  interface Window {
    midas: MidasContainer;
    selectionShelf: SelectionShelf;
    profilerShelf: ProfilerShelf;
  }
}


export function load_ipython_extension() {
  Jupyter.notebook.events.on("kernel_connected.Kernel", function() {
      tearDownMidasComponent();
  });

  LogSteps("Kernel starting, opening recovery comm");
  function checkIfNull() {
    if (Jupyter.notebook.kernel === null) {
       console.log("The kernel is null. Trying again in 100 milliseconds.");
       window.setTimeout(checkIfNull, 100);
    } else {
      openRecoveryComm();
      makeComm();
    }
  }
  checkIfNull();
}