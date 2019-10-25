import React, {RefObject} from "react"; 
import MidasContainer from "./MidasContainer";
import MidasMidbar from "./MidasMidbar";

export class MidasSideBar extends React.Component<{}, {}> {

  childRef: any;

  constructor(props?: {}) {
    super(props);

    this.setRef = this.setRef.bind(this);
  }

  setRef(input: MidasContainer) {
    this.childRef = input;
  }

  getRef() {
    return this.childRef;
  }

  render() {
    return (
      <>
      <div id="midas-resizer"></div>
      <div className="midas-inside">
        <MidasMidbar></MidasMidbar>
        <MidasContainer ref={this.setRef}></MidasContainer>
      </div>
      </>
    );
  }
}
