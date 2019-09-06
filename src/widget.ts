/// <reference path="./external/Jupyter.d.ts" />
import { vegaEmbed } from "./index";
import { DOMWidgetView, JupyterPhosphorPanelWidget } from "@jupyter-widgets/base";
// import {Jupyter} from  "@jupyter/base";
// var events = require("js/base/events");
import { LogInternalError, LogDebug } from "./utils";
import { addDataFrame } from "./midas";
import { SELECTION_SIGNAL, DEBOUNCE_RATE, Y_SCALE, Y_DOMAIN_SIGNAL } from "./constants";

interface WidgetUpdate {
  key: string;
  remove?: string;
  insert?: any[];
}

enum WidgeMessageType {
  update = "update",
  registerSignal = "registerSignal"
}

interface WidgetMessageBase {
  type: WidgeMessageType;
}

interface WidgetUpdateMessage extends WidgetMessageBase {
  updates: WidgetUpdate[];
}

interface SignalCallback {
  signal: string;
  // this will be a function, (name, value) => { }, but will be parsed as string.
  // and the code should just pass in the body of the function
  // see https://vega.github.io/vega/docs/api/view/#signals
  callback: string;
}

interface WidgetRegisterSignalMessage extends WidgetMessageBase {
  callbacks: SignalCallback[];
}

const casted_window = (window as any);
if (typeof casted_window.lastInvoked === "undefined") {
  casted_window.lastInvoked = new Date();
  casted_window.lastInvokedTimer = null;
}

// type WidgetMessage = WidgetUpdateMessage | WidgetRegisterSignalMessage ;

export class MidasWidget extends DOMWidgetView {
  // hm, fixme: not sure why this view's type is any???
  view: any;
  viewElement: HTMLDivElement;
  errorElement: any;

  render() {
    // this.viewElement = document.createElement("div");
    let widgetID = this.model.get("widgetID");

    // this.el.appendChild(this.viewElement);

    this.errorElement = document.createElement("div");
    this.errorElement.style.color = "red";
    this.el.appendChild(this.errorElement);

    const dfName = this.model.get("dfName");
    const reembed = () => {
      if (this.view) {
        this.view.finalize();
        this.view = null;
      }
      const spec = JSON.parse(this.model.get("_spec_source"));
      const opt = JSON.parse(this.model.get("_opt_source"));

      if (spec == null) {
        return;
      }

      vegaEmbed(`#midas-element-${widgetID}`, spec, {
        loader: { http: { credentials: "same-origin" } },
        ...opt
      })
        .then((res: any) => {
          this.view = res.view;
          // also update this view such that it calls the Midas tick everytime it changes...
          LogDebug(`Registering signal for TICK`);
          this.view.signal(SELECTION_SIGNAL, () => { window.midas.tick(dfName); });
          this.send({ type: "display" });
        })
        .catch((err: Error) => console.error(err));
    };

    const checkView = () => {
      if (this.view == null) {
        throw new Error("Internal error: no view attached to widget");
      }
    };

    const applyUpdate = async (update: WidgetUpdate) => {
      checkView();
      const filter = new Function(
        "datum",
        "return (" + (update.remove || "false") + ")"
      );
      const newValues = update.insert || [];
      const changeSet = this.view
        .changeset()
        .insert(newValues)
        .remove(filter);

      await this.view.change(update.key, changeSet).runAsync();
    };

    const registerSignalCallback = (signalCallback: SignalCallback) => {
      checkView();
      // we know that there are two arguments, name and value
      const cb = new Function("name", "value", signalCallback.callback);
      const wrapped = (name: any, value: any) => {
        const n = new Date();
        const l = (window as any).lastInvoked;
        (window as any).lastInvoked = n;
        if (l) {
          if ((n.getTime() - l.getTime()) < DEBOUNCE_RATE) {
            clearTimeout((window as any).lastInvokedTimer);
          }
          (window as any).lastInvokedTimer = setTimeout(() => cb(name, value), DEBOUNCE_RATE);
        } else {
          throw Error("global times should be kept");
        }
      };
      this.view.addSignalListener(signalCallback.signal, wrapped);
    };

    this.model.on("change:_spec_source", reembed);
    this.model.on("change:_opt_source", reembed);

    // FIXME: add some error checking
    this.model.on("msg:custom", async (ev: any) => {
      if (!ev.type) {
        LogInternalError(`custom message does not have type information`);
        return;
      }
      switch (ev.type) {
        case WidgeMessageType.update: {
          const message = ev as WidgetUpdateMessage;
          for (const update of message.updates) {
            await applyUpdate(update);
          }
          return;
        }
        case WidgeMessageType.registerSignal: {
          console.log("Got request to register signal", ev);
          const message = ev as WidgetRegisterSignalMessage;
          for (const callback of message.callbacks) {
            registerSignalCallback(callback);
          }
          return;
        }
        default:
          LogInternalError(`Not all cases handled`);
      }
    });
    // initial rendering
    let fixYScale = () => {
      console.log("FIXING Y");
        // access the current scale
        // @ts-ignore
        const y_scale = this.view.scale(Y_SCALE);
        // then set the current scale
        this.view.signal(Y_DOMAIN_SIGNAL, y_scale.domain());
    };
    // must be called here, otherwise we have asyn issues..
    addDataFrame(widgetID, dfName, fixYScale, () => reembed());

  }
}
