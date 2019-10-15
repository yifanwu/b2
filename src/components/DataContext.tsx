import React from "react";

// prob some configurations
interface DataContextProps {

}

interface DataContextState {

}

// this div contains all the columns of interest
export default class DataContext extends React.Component<DataContextProps, DataContextState> {
  constructor(props: any) {
    super(props);
    this.addColumn = this.addColumn.bind(this);
    this.state = {};
  }

  addColumns() {

  }

  // we need to know which column and what df
  addColumn() {

  }

  // this is add join information
  addLinking() {
    
  }

  // contextual information
  addContext() {

  }

  render() {
    return (<div>
      
    </div>);
  }
}