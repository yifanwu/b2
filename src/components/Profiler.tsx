import React from "react";
// for now the profiler is just going to be a table of the first 5 results
// and the user can click to say not interesting

import DataExplorer from "@nteract/data-explorer";
import { DataProps } from "@nteract/data-explorer/src/types";

interface ProfilerProps {
  data: DataProps;
}

interface ProfilerState {
}

export default class Profiler extends React.Component<ProfilerProps, ProfilerState> {
  constructor(props: ProfilerProps) {
    super(props);
    this.state = {};
  }

  render() {
    return (<div style={{"width": 400}}>
        <DataExplorer
          data={this.props.data}
          initialView="grid"
          mediaType="application/vnd.dataresource+json"
          metadata={{dx: {}}}
        />
      </div>);
  }
}